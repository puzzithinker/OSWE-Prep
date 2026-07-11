# .NET Deserialization Methodology Guide

**Goal**: White-box identification → key/material recovery → ysoserial.net weaponization → reliable RCE PoC for OSWE-style targets.

**Companion materials**:
- `poc-examples/dotnet-viewstate-deserialization/`
- `notes/DOTNET-VIEWSTATE-DESERIALIZATION.md`
- `notes/DOTNETNUKE-COOKIE-DESERIALIZATION.md`

---

## Overview

.NET applications serialize object graphs for ViewState, session/personalization cookies, remoting, and APIs. Dangerous formatters + attacker control of bytes + gadgets in loaded assemblies = **RCE**.

Primary exam skills:
1. Spot deserialize sinks and ViewState usage quickly.
2. Recover **machineKey** / understand MAC/encryption.
3. Drive **ysoserial.net** with correct formatter + algorithms.
4. Script delivery and OOB verification in Python.

---

## Part 1: Identifying deserialization

### White-box greps

```bash
grep -Rn "BinaryFormatter" --include='*.cs' .
grep -Rn "ObjectStateFormatter\|LosFormatter\|NetDataContractSerializer" --include='*.cs' .
grep -Rn "TypeNameHandling" --include='*.cs' .
grep -Rn "Deserialize(" --include='*.cs' . | head
grep -Rn "machineKey\|enableViewStateMac" --include='*.config' .
```

Use **dnSpy / ILSpy** on shipped DLLs when source is incomplete.

### Vulnerable patterns

```csharp
// BinaryFormatter — historically catastrophic on untrusted input
var bf = new BinaryFormatter();
var obj = bf.Deserialize(stream);

// ViewState path (framework) — forgeable if keys known
// ObjectStateFormatter / LosFormatter under the hood

// JSON.NET anti-pattern
var settings = new JsonSerializerSettings {
    TypeNameHandling = TypeNameHandling.All
};
JsonConvert.DeserializeObject(userJson, settings);
```

### Black-box signals

| Signal | Meaning |
|--------|---------|
| `__VIEWSTATE` hidden field | Classic ASP.NET pages |
| Base64 `/wEP...` | Common ViewState prefix |
| IIS + `X-AspNet-Version` | Stack fingerprint |
| Opaque cookies that break when modified | Signed/encrypted serialized state |
| `.aspx` postbacks | ViewState processed |

---

## Part 2: ViewState deep dive

### Logical structure

```text
Client POST
  __VIEWSTATE = Base64(
      [optional encrypt](
          MAC(
              serialized_page_state
          )
      )
  )
```

Server validates MAC (if enabled), decrypts, deserializes.

### machineKey

```xml
<machineKey
  validationKey="HEX..."
  decryptionKey="HEX..."
  validation="SHA1|HMACSHA256|..."
  decryption="AES|DES|3DES" />
```

**Key hunting order**:
1. `web.config` in site and parents  
2. `machine.config` (server-wide — less common to have secrets you can read remotely)  
3. Backups, `.git`, deployment exports, installer defaults  
4. Historical product CVEs with hard-coded keys (e.g. training discussions of Exchange-class issues)

### enableViewStateMac

- `true` (default modern): need valid MAC → need key  
- `false`: much easier forgery (rare in hardened apps)

### VIEWSTATEGENERATOR

Some payloads require correct generator value from the page. Always capture a legitimate page first.

---

## Part 3: Other channels

| Channel | Notes |
|---------|-------|
| ViewState | Most common training target |
| Cookies (DNN personalization, etc.) | May use different formatter; still ysoserial gadgets |
| `BinaryFormatter` on body/file | Direct file/upload/API |
| `.NET remoting` / HMI | Less common on web exam but same class |
| JSON.NET type handling | `ObjectDataProvider`-class gadgets via JSON |

Treat each as: **find bytes → find how integrity works → emit gadget → deliver**.

---

## Part 4: ysoserial.net

### Install

Download releases from the official GitHub project (`pwntester/ysoserial.net`). Run on Windows preferred; some use Wine/Mono with limitations.

### ViewState plugin pattern

```text
ysoserial.exe -p ViewState -g ObjectDataProvider -c "cmd /c whoami" ^
  --validationkey=HEX --validationalg=SHA1 ^
  --decryptionkey=HEX --decryptionalg=AES ^
  --generator=GENERATOR --path=/page.aspx
```

Flags vary by ysoserial.net version — run `-h` and match your lab notes.

### Useful gadgets (high level)

| Gadget | Role |
|--------|------|
| ObjectDataProvider | Very common; invokes methods via type converters |
| TypeConfuseDelegate | Powerful delegate confusion chains |
| PSObject | PowerShell-oriented |
| WindowsIdentity | Claims/token related scenarios |

Understand **ObjectDataProvider**: it is designed to invoke methods when properties are set — perfect for gadget chains.

### Formatter selection

| Formatter | Typical use |
|-----------|-------------|
| ViewState plugin | ASP.NET pages |
| BinaryFormatter | Raw BF sinks |
| LosFormatter | ViewState-related legacy |
| SoapFormatter / DataContract | Service stacks |

---

## Part 5: Exploitation workflow (OSWE timing)

| Step | Action | Budget |
|------|--------|--------|
| 1 | Confirm ASP.NET + ViewState/cookie | 5 min |
| 2 | Source/config for keys & sinks | 10–20 min |
| 3 | First OOB (`ping` / HTTP) | 15 min |
| 4 | Reverse shell or aspx write | 20–40 min |
| 5 | Python PoC stages | 30–60 min |

### Verification ladder

1. ICMP/DNS/HTTP callback (proves code exec)  
2. `whoami` to web-accessible file  
3. Interactive shell  

Never jump to complex shells before OOB proof.

---

## Part 6: Python PoC patterns

```text
stages:
  recon: GET page, extract __VIEWSTATE, __VIEWSTATEGENERATOR, cookies
  prepare: subprocess ysoserial.net with keys from args/config
  exploit: POST malicious viewstate
  verify: poll callback server or fetch marker file
```

Design argparse for:

- `--url` / host/port  
- `--validationkey` `--decryptionkey` `--validationalg` `--decryptionalg`  
- `--command` or `--lhost/--lport`  
- `--proxy`  

Mirror structure of `poc-examples/java-deserialization-commons/poc.py`.

---

## Part 7: Code review checklist

- [ ] Any `BinaryFormatter` on external data?  
- [ ] JSON.NET `TypeNameHandling` not `None`?  
- [ ] ViewState MAC disabled?  
- [ ] Hard-coded machineKey?  
- [ ] Custom cookie serialization?  
- [ ] Upload of `.rem` / serialized files?  
- [ ] Old CMS modules with known deserial bugs?  

### Safe directions

- Prefer DTOs + `System.Text.Json` without type name handling  
- Server-side session IDs only  
- Strong unique machineKeys; secret store not world-readable  
- Remove unused assemblies (gadget reduction)

---

## Part 8: Bypasses and edge cases

| Problem | Approach |
|---------|----------|
| Unknown alg | Try common pairs SHA1+AES, HMACSHA256+AES |
| Cookie length limits | Switch to ViewState or body channel |
| Encryption on | Must have decryptionKey; don't strip blindly |
| AV kills payload | Quieter command; write file; living-off-land |
| No outbound | Write aspx under site root; fetch via HTTP |
| Partial trust historical | Less relevant modern; still check errors |

---

## Part 9: OSWE exam strategy

1. **Decompile early** on .NET targets — guessing wastes hours.  
2. Keep a **ysoserial cheat strip** in Exam-Day-Runbook.  
3. Separate “got RCE” from “pretty shell” under time pressure.  
4. DNN-style cookie bugs and ViewState are siblings — same report structure.  
5. Document key source (which file) in report methodology without unnecessary secret sprawl.

### Common mistakes

- Wrong validation algorithm  
- Forgetting VIEWSTATEGENERATOR  
- Testing GET only when postback required  
- Using Linux reverse shell syntax on Windows  
- Not URL-encoding / Base64 issues in transit  

---

## Part 10: Quick reference

### Grep pack

```text
BinaryFormatter|LosFormatter|ObjectStateFormatter|TypeNameHandling|machineKey|__VIEWSTATE
```

### First payload philosophy

```text
ping / iwr callback  →  then shell
```

### Related repo paths

| Path | Why |
|------|-----|
| `poc-examples/dotnet-viewstate-deserialization/` | Working example |
| `notes/DOTNETNUKE-COOKIE-DESERIALIZATION.md` | Cookie channel case |
| `guides/Chain-Decision-Trees.md` | After RCE pivots |
| `guides/Dangerous-Sinks-Cheatsheet.md` | First-pass greps |

---

## References

- ysoserial.net (pwntester)  
- Black Hat: Friday the 13th – JSON Attacks  
- Microsoft guidance: BinaryFormatter obsolete / dangerous  
- Alvaro Muñoz talks on .NET deserial (README links)  
