# PHP Object Injection Case Study

## Environment
**Application**: WordPress 5.0 with vulnerable plugin
**PHP**: 7.2

## Vulnerable Code
```php
// Unserializing user-controlled cookie
$user_data = unserialize($_COOKIE['user_data']); // VULNERABLE
```

## Chain Outline
1. Identify unserialize() on cookie data
2. Find classes with __destruct containing file operations
3. Build POP chain: ClassA::__destruct → ClassB::__toString → system()
4. Generate serialized payload
5. Submit via cookie
6. Achieve RCE when __destruct is called

## Findings
**Root Cause**: unserialize() on untrusted data + exploitable magic methods
**Fix**: Never unserialize untrusted data, use JSON instead, implement __wakeup validation
