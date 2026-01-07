# Node.js Deserialization Case Study

## Environment
**Application**: Express.js 4.16 with node-serialize
**Node**: v10.x

## Vulnerable Code
```javascript
var serialize = require('node-serialize');
var userData = req.cookies.profile;
var obj = serialize.unserialize(userData); // VULNERABLE
```

## Chain Outline
1. Identify node-serialize usage in cookies
2. Create IIFE payload with child_process
3. Wrap with _$$ND_FUNC$$_ marker
4. Send via cookie
5. RCE when unserialize() is called

## Findings
**Root Cause**: node-serialize allows function serialization without validation
**Fix**: Don't use node-serialize, validate input, use JSON.parse() instead
