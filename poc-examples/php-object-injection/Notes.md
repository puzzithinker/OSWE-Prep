# PHP Object Injection RCE PoC Notes

## Vulnerability Summary
- **Target**: PHP applications using unserialize() on untrusted data
- **Type**: PHP Object Injection → POP Chain → RCE
- **Impact**: Remote code execution

## Key Concepts
PHP magic methods (__wakeup, __destruct, __toString, __call) are automatically invoked during object lifecycle. Attackers chain these methods to achieve code execution.

## Lab Setup
```bash
# LAMP stack with vulnerable WordPress plugin
# Or custom PHP application with unserialize()
```

## OSWE Exam Tips
- Search for `unserialize($_` in source code
- Identify classes with dangerous magic methods
- Build POP chains manually by analyzing class relationships
- Common chains: File write → Include, Command injection via system()

## References
- OWASP: https://owasp.org/www-community/vulnerabilities/PHP_Object_Injection
- POP Chain Construction: https://www.exploit-db.com/docs/english/44756-deserialization-vulnerability.pdf
