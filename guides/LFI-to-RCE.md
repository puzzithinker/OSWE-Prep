# LFI → RCE Methodology

**Goal**: Turn local file inclusion / path traversal read into remote code execution for OSWE-style chains.

**Companions**: `guides/File-Upload-to-RCE.md`, `guides/Chain-Decision-Trees.md`, `guides/XXE-Attack-Vectors.md` (file read sibling).

---

## 1. LFI vs related bugs

| Bug | Effect |
|-----|--------|
| LFI | Server **includes/executes** local file as code (PHP `include`) |
| Path traversal read | Reads file contents (may not execute) |
| RFI | Includes **remote** URL (often disabled) |
| XXE file read | XML layer file disclosure |

RCE usually needs **include of attacker-controlled content** or **log/session poisoning**.

---

## 2. Finding LFI (white-box)

```bash
grep -Rn 'include\s*(\|require\s*(\|include_once\|require_once' --include='*.php' .
grep -Rn 'file_get_contents\s*(\|readfile\s*(\|fopen\s*(' --include='*.php' .
# Java
grep -Rn 'new File(\|Files.read\|getResourceAsStream' --include='*.java' .
```

Patterns:

```php
include($_GET['page'] . '.php');
include($lang); // from cookie
```

---

## 3. Confirmation

- Traverse to known files: `/etc/passwd`, `C:\Windows\win.ini`, app `config.php`  
- Observe content in response or errors  
- Note prefix/suffix (`.php` append) — null byte historical, wrappers, path truncation  

---

## 4. Path to RCE techniques

### A. Log poisoning

1. Inject PHP into logs via User-Agent / URL  
2. Include log path through LFI  
3. Execute injected PHP  

Requirements: know log path; logs readable by app user; include executes as PHP.

### B. Session file inclusion

1. Plant PHP in session data (user-controlled field stored in session)  
2. Include `/var/lib/php/sessions/sess_<id>`  

### C. Upload + include

1. Upload non-executable polyglot (`image/shell.jpg` with PHP)  
2. LFI includes it → executed as PHP  

**Extremely common chain** with weak uploads.

### D. Proc / env / pearcmd (environment-specific)

Advanced PHP wrappers (`php://filter`, `php://input`, `data://`, `expect://` if enabled). Test carefully; many disabled.

```text
php://filter/convert.base64-encode/resource=index.php  # source disclosure
```

### E. Config overwrite / autoload

Less common: include composer autoload paths after writing files via other bugs.

---

## 5. PHP wrappers cheat (study)

| Wrapper | Use |
|---------|-----|
| `php://filter` | Base64 source disclosure |
| `php://input` | Include POST body as PHP (if allow_url_include etc.) |
| `data://` | Inline payload |
| `phar://` | Deserial side quests |
| `zip://` | Include file inside zip |

Exact enablement is environment-specific.

---

## 6. Chain playbooks

### Upload filtered + LFI

```text
Upload .jpg webshell polyglot → discover path → LFI include path → RCE
```

### No upload + LFI

```text
Poison access log / session → include → RCE
```

### LFI read-only (no exec)

```text
Read creds/config → reuse elsewhere (DB, admin password, machineKey)
```

Still valuable without direct RCE.

---

## 7. PoC stages

```text
recon_params()
confirm_passwd()
disclose_source_via_filter()  # optional
plant_payload()               # upload / log / session
include_payload()
verify_exec()
```

---

## 8. Defenses

1. Never include user input; use allow-list map `page=home→home.php`  
2. Disable dangerous wrappers; open_basedir  
3. Store uploads outside docroot; random names; no PHP in upload dirs  
4. Harden log paths; don’t store raw UA in includable locations  
5. Least privilege file permissions  

---

## 9. OSWE tactics

- LFI often **pairs** with upload filters — learn both.  
- Source disclosure via `php://filter` accelerates finding next vuln.  
- Time box log poisoning path discovery (distro-specific paths).  
- On Java, “LFI” may be path traversal read only — pivot to other RCE.  

**Related**: File-Upload guide, Chain decision trees, PHP deserial (phar).
