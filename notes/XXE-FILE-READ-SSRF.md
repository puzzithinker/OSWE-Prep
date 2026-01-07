# XXE File Read and SSRF Case Study

## Environment
**Application**: Custom Java Spring Boot API
**XML Parser**: DocumentBuilder (JDK 8)
**URL**: http://192.168.1.100:8080/api/process
**Method**: POST with XML body

## Recon
**Entry Points**: POST /api/process accepts Content-Type: application/xml
**Vulnerable Code**: XMLController.java - DocumentBuilder without secure configuration

### Vulnerable Pattern
```java
@PostMapping("/api/process")
public ResponseEntity<String> processXml(@RequestBody String xml) {
    DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
    Document doc = dbf.newDocumentBuilder().parse(new InputSource(new StringReader(xml)));
    // Processing...
}
```

## Vulnerability Hypothesis
**Class**: XML External Entity Injection (CWE-611)
**Data Flow**: HTTP POST → XML Parser → External Entity Resolution
**Preconditions**: External entities enabled (default in many parsers)

## Chain Outline
1. Test entity expansion with simple payload
2. Read /etc/passwd via file:// protocol
3. Setup callback server for out-of-band exfiltration
4. Exfiltrate /etc/shadow via external DTD
5. SSRF to AWS metadata service
6. Retrieve IAM credentials via SSRF

## Evidence
- Screenshots/tcpdump showing callbacks
- Retrieved file contents
- AWS metadata responses

## Findings
**Root Cause**: DocumentBuilderFactory created without secure configuration
**Fix**:
```java
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
dbf.setFeature("http://xml.org/sax/features/external-general-entities", false);
dbf.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
```
