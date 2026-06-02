# PHP Object Injection Case Study

## Environment

- Host OS: Kali (attacker), Ubuntu 18.04/20.04 or XAMPP (target)
- App: Any PHP app using `unserialize()` on user input (WordPress plugins, custom apps, older frameworks like old Symfony/Monolog combos)
- PHP: 5.x – 7.x (magic methods behavior consistent; 8.x has some changes but still vulnerable if code present)
- Web URL: http://target/
- Key ports: 80/443
- Database: Often MySQL (for apps like WordPress), but not required for pure POP RCE

**Common vulnerable apps for practice**:
- Old WordPress + vulnerable plugin/theme with custom unserialize
- Custom "profile" or "session" handlers
- See references to phpggc for real chains against popular libs

## Recon

- Entry points: `$_COOKIE`, `$_POST`, `$_GET` (base64 encoded often), any parameter fed to `unserialize()`. Also `phar://` wrappers in file functions.
- Roles/privileges: Usually works from unauthenticated or low-priv context; RCE gives web server user (www-data, apache, etc.).
- Render locations / sinks: `unserialize( $data )`, `unserialize( base64_decode(...) )`, sometimes inside `session_decode` or custom deserializers. Also any `file_get_contents('phar://...')`, `include`, `file_exists` etc. that can trigger PHAR metadata deserial.

**White-box search**:
```bash
grep -r "unserialize" --include="*.php" .
grep -r "phar://" --include="*.php" .
```

**Black-box**: Look for cookies that start with `O:`, `a:`, or base64 that decodes to serialized objects. Length or structure changes when you tamper.

## Vulnerability Hypothesis

- Suspected class: PHP Object Injection (insecure deserialization via unserialize).
- Data flow: Attacker-controlled serialized string → `unserialize()` → PHP reconstructs objects → magic methods (`__wakeup`, `__destruct`, `__toString`, `__call`, etc.) fire automatically in defined order → dangerous side effects (system(), file write, SQL, etc.).
- Preconditions:
  - At least one class with a dangerous magic method is loaded in the current request scope (autoloader helps).
  - No `__wakeup` / `__destruct` guards or `allowed_classes` filter (PHP 7+).
  - For PHAR: a file operation using a user-controlled path with `phar://` wrapper.

## Chain Outline

1. **Identify injection point** and confirm unserialize on attacker data.
2. **Source review / class discovery**: Find all classes with magic methods (especially those doing file ops, eval/system, SQL concat, include).
3. **Build POP chain on paper**: Choose starting object whose magic method passes attacker-controlled properties to the next object's magic method.
4. **Instantiate & set properties**: Create the gadget objects, set public/protected properties to point to next gadget or payload string.
5. **Serialize** the root object (often `serialize($obj)` or via phpggc).
6. **Encode & deliver** (cookie, POST, GET param, sometimes file upload name or other).
7. **Trigger**: Next request that causes unserialize (or file op for PHAR) executes the chain.
8. **Verify** + escalate (reverse shell, webshell drop, etc.).

## Evidence

- Screenshots: Serialized blob in request (look for `O:xx:"ClassName":yy:{...}`), response or callback.
- Logs: Web server error logs may show command output or "system()" calls; PHP errors if classes missing.
- Artifacts: Generated `.phar` files for PHAR vectors; base64 of payload for transport.

## Findings

### Root Cause
`unserialize()` on completely untrusted data reconstructs live objects with attacker-controlled property values. PHP's magic methods act as "gadgets". Chaining them (Property Oriented Programming) lets you reach powerful primitives like `system()` without the original developer ever intending executable code paths.

No type checks, no allow-list by default (until `unserialize(..., ['allowed_classes' => [...]])` in PHP 7+ which is often not used).

### Vulnerable Code Patterns

```php
// Classic cookie
$data = unserialize($_COOKIE['auth'] ?? '');

// Base64 wrapped (very common)
$obj = unserialize(base64_decode($_GET['data']));

// In a "safe" looking session handler or cache
$profile = unserialize($db_row['profile_data']);

// PHAR trigger (any of these with user-controlled path)
file_get_contents($_GET['file']);
include($_GET['template']);
file_exists($user_path);
```

### Magic Methods to Hunt

- `__destruct()` — fires at end of request, great for file write/delete, system.
- `__wakeup()` — fires during unserialize, good for init side effects.
- `__toString()` — fires when object used as string (SQL, echo, file paths).
- `__call()` / `__get()` / `__set()` — property/method proxying.
- `__invoke()` — callable objects.

### Example Simple POP (Conceptual)

(See full examples in `poc-examples/php-object-injection/Notes.md` and guides/PHP-Deserialization-Patterns.md)

A typical minimal chain for command exec often looks like Monolog or Symfony gadgets when those libs are present:

```php
// Attacker controls $this->data or similar in a chain that eventually does
system($this->command);
```

### PHAR Deserialization (Powerful Variant)

Even if `unserialize()` is not directly callable on user input, if the app does file operations on a user-influenced filename:

```php
// Create evil.phar with serialized metadata containing gadget object
$phar = new Phar('evil.phar');
$phar->startBuffering();
$phar->addFromString('x', 'test');
$phar->setStub('<?php __HALT_COMPILER(); ?>');
$phar->setMetadata(new GadgetClass());  // POP object here
$phar->stopBuffering();
```

Then force the app to do `include('phar://uploads/evil.phar/anyfile')` or similar via path traversal / file upload rename.

This bypasses direct unserialize sinks.

### Fix Ideas

**Best**:
- Never call `unserialize()` on user-controlled data. Use `json_decode(..., true)` + strict schema validation / typed DTOs.
- If you must support legacy serialized data, pass `['allowed_classes' => ['Only','Safe','Classes']]` (PHP 7.0+).
- Implement `__wakeup()` that throws or clears dangerous properties.

**For PHAR**:
- Never let user-controlled data reach `phar://`, `zip://`, `glob://` etc. wrappers.
- Validate / sanitize / prefix all file paths used in file functions.
- Disable dangerous wrappers in php.ini where possible (`disable_functions`, `open_basedir`).

**Defense in depth**:
- Least privilege for web user.
- WAF signatures for `O:`, typical serialized prefixes, and `phar://`.
- Regular `phpggc` and dependency scanning (Monolog, Symfony, SwiftMailer, etc. have known chains).

### Exam-Relevant Variations
- Apps that unserialize inside an autoloaded class scope (more gadgets available).
- Multiple steps: first injection populates a DB field or file, later privileged action triggers it.
- Combined with file upload (upload a .phar disguised, then trigger via include or file op).

## OSWE Exam Tips

- **Code review order**: 1) Find every `unserialize`. 2) Find every class with magic methods. 3) Map which properties flow into dangerous calls. 4) Build the shortest chain on paper. 5) Test serialization locally in a throwaway PHP snippet.
- **phpggc is your friend** for real apps (generates payloads for known libs): `phpggc -l`, then adapt.
- For custom apps you usually build the chain manually — practice this!
- Payload size can get large; watch cookie limits or use POST/GET with base64.
- Verify with a benign side effect first (e.g. file write to /tmp/you_were_here) before reverse shell.
- Common blocker: Classes not in scope at unserialize time (need the right `require` or autoloader to have loaded the gadget classes).
- Time management: If source is large, use `grep -r` + editor "find in files" aggressively. Don't read every file linearly.

## Quick Manual Test (Local PHP)

```php
<?php
class Test { public $cmd; function __destruct() { system($this->cmd); } }
echo base64_encode(serialize(new Test()));
?>
```

Set the resulting string as the cookie/param and watch for command execution.

## References

- OWASP PHP Object Injection: https://owasp.org/www-community/vulnerabilities/PHP_Object_Injection
- PHPGGC (must-have): https://github.com/ambionics/phpggc
- PHAR deserial deep dive: https://blog.checkpoint.com/2019/02/13/phar-deserialization-vulnerabilities-in-php/
- `poc-examples/php-object-injection/` (PoC + rich Notes.md)
- `guides/PHP-Deserialization-Patterns.md`
- `notes/ATUTOR-2.2.1-*` for real chaining examples that include PHP object or type juggling + RCE

See also the detailed lab manual in `poc-examples/php-object-injection/Notes.md` for payload generation and debugging.
