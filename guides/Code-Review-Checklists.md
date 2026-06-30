# Code Review Checklists for OSWE

## Overview
This guide provides comprehensive checklists for identifying vulnerabilities during white-box code review. Organized by language and vulnerability type with time-optimized strategies for OSWE exam conditions.

## Part 1: Dangerous Functions by Language

### PHP

**Command Injection**:
```php
system()           // Execute command, output directly
exec()             // Execute command, return last line
passthru()         // Execute command, output raw binary
shell_exec()       // Execute command, return full output
``                 // Backticks, same as shell_exec()
popen()            // Open process file pointer
proc_open()        // Execute command with pipes
pcntl_exec()       // Execute program in current process space
```

**Code Injection**:
```php
eval()             // Evaluate string as PHP code
assert()           // Evaluate assertion (can execute code)
create_function()  // Deprecated, creates lambda function
preg_replace('/e') // Deprecated 'e' modifier executes code
include()          // Include and execute file
require()          // Require and execute file
include_once()     // Include file once
require_once()     // Require file once
```

**SQL Injection**:
```php
mysql_query()      // Deprecated, no prepared statements
mysqli_query()     // Can be vulnerable if not parameterized
pg_query()         // PostgreSQL, can be vulnerable
mssql_query()      // MSSQL, can be vulnerable
$pdo->query()      // PDO, vulnerable if used with concatenation
$pdo->exec()       // PDO, vulnerable if used with concatenation
```

**File Operations**:
```php
file_get_contents() // Read file contents
file_put_contents() // Write to file
fopen()            // Open file or URL
readfile()         // Output file
file()             // Read file into array
unlink()           // Delete file
copy()             // Copy file
move_uploaded_file() // Move uploaded file
rename()           // Rename file
```

**Deserialization**:
```php
unserialize()      // Unserialize data - VERY DANGEROUS
```

**XML Parsing**:
```php
simplexml_load_string() // Parse XML string
simplexml_load_file()   // Parse XML file
DOMDocument::loadXML()  // Load XML
XMLReader::XML()        // Read XML
```

### Python

**Command Injection**:
```python
os.system()        # Execute command in subshell
os.popen()         # Open pipe to/from command
os.exec*()         # Replace process with command
subprocess.call()  # Execute command (safer with list)
subprocess.Popen() # Execute command (check shell=True)
eval()             # Evaluate expression
exec()             # Execute code
compile()          # Compile code
__import__()       # Dynamic import
```

**SQL Injection**:
```python
cursor.execute()   # Vulnerable if using string formatting
cursor.executemany() # Vulnerable if using string formatting
# VULNERABLE: cursor.execute("SELECT * FROM users WHERE id = " + user_id)
# SAFE: cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

**Deserialization**:
```python
pickle.loads()     # Deserialize pickle data - VERY DANGEROUS
pickle.load()      # Deserialize from file - VERY DANGEROUS
yaml.load()        # Unsafe YAML load (use yaml.safe_load)
marshal.loads()    # Internal serialization, dangerous
jsonpickle.decode() # JSON pickle deserialization
```

**Template Injection**:
```python
render_template_string() # Jinja2, vulnerable if user input
Template().render()      # Jinja2/Mako, vulnerable
str.format()             # Format string, potential info leak
```

**File Operations**:
```python
open()             # Open file
os.remove()        # Delete file
os.rename()        # Rename file
shutil.copy()      # Copy file
pathlib.Path()     # Path operations
```

### Java

**Command Injection**:
```java
Runtime.exec()              // Execute command
ProcessBuilder.start()      // Start process
ScriptEngineManager.eval()  // Execute script
```

**Deserialization**:
```java
ObjectInputStream.readObject()     // Deserialize object - DANGEROUS
XMLDecoder.readObject()            // XML deserialization - DANGEROUS
XStream.fromXML()                  // XML deserialization - DANGEROUS
Gson.fromJson()                    // Generally safe, check TypeToken
Jackson.readValue()                // Safe with default typing disabled
```

**SQL Injection**:
```java
Statement.execute()          // Vulnerable if using concatenation
Statement.executeQuery()     // Vulnerable if using concatenation
PreparedStatement.execute()  // SAFE if placeholders used
// VULNERABLE: stmt.execute("SELECT * FROM users WHERE id = " + userId)
// SAFE: PreparedStatement pstmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?")
```

**Code Injection**:
```java
Class.forName()              // Dynamic class loading
ClassLoader.loadClass()      // Load class dynamically
Method.invoke()              // Reflection method call
ScriptEngine.eval()          // Evaluate script
```

**XML Parsing**:
```java
DocumentBuilder.parse()           // XXE vulnerable
SAXParser.parse()                 // XXE vulnerable
XMLStreamReader.parse()           // XXE vulnerable
Unmarshaller.unmarshal()          // XXE vulnerable (JAXB)
```

### C# / .NET

**Command Injection**:
```csharp
Process.Start()                  // Start process
ProcessStartInfo()              // Process configuration
```

**Deserialization**:
```csharp
BinaryFormatter.Deserialize()        // VERY DANGEROUS
ObjectStateFormatter.Deserialize()   // ViewState - DANGEROUS
JavaScriptSerializer.Deserialize()   // Can be dangerous
JsonConvert.DeserializeObject()      // Check TypeNameHandling
XmlSerializer.Deserialize()          // Generally safer
```

**SQL Injection**:
```csharp
SqlCommand.ExecuteReader()       // Vulnerable if concatenation
SqlCommand.ExecuteNonQuery()     // Vulnerable if concatenation
SqlDataAdapter.Fill()            // Vulnerable if concatenation
// VULNERABLE: cmd.CommandText = "SELECT * FROM users WHERE id = " + userId
// SAFE: cmd.Parameters.AddWithValue("@id", userId)
```

**Code Injection**:
```csharp
CodeDomProvider.CompileAssembly()  // Compile code
Assembly.Load()                     // Load assembly
Type.GetType()                      // Get type by name
Activator.CreateInstance()          // Create instance dynamically
```

### JavaScript / Node.js

**Command Injection**:
```javascript
child_process.exec()        // Execute command in shell - DANGEROUS
child_process.spawn()       // Safer if no shell
eval()                      // Evaluate code - DANGEROUS
Function()                  // Create function from string - DANGEROUS
setTimeout/setInterval()    // Can execute strings - DANGEROUS
vm.runInContext()           // Run code in VM context
```

**Deserialization**:
```javascript
JSON.parse()                // Generally safe for JSON
serialize/unserialize       // node-serialize - DANGEROUS
eval() on serialized data   // VERY DANGEROUS
```

**Code Injection**:
```javascript
eval()                      // Evaluate code
new Function()              // Create function
require()                   // Dynamic require can be dangerous
vm.runInNewContext()        // Execute code in sandbox
```

**Template Injection**:
```javascript
_.template()                // Lodash template
Handlebars.compile()        // Handlebars template
ejs.render()                // EJS template
pug.compile()               // Pug template
```

## Part 2: Source/Sink Identification

### Data Flow Analysis

**Sources** (User-Controlled Input):
```
# HTTP
$_GET, $_POST, $_REQUEST, $_COOKIE, $_FILES (PHP)
request.args, request.form, request.cookies, request.files (Python/Flask)
HttpServletRequest.getParameter() (Java)
Request.QueryString, Request.Form, Request.Cookies (ASP.NET)
req.query, req.body, req.params, req.cookies (Node.js/Express)

# Headers
$_SERVER['HTTP_*'] (PHP)
request.headers (Python)
request.getHeader() (Java)
Request.Headers (ASP.NET)
req.headers (Node.js)

# Files
file_get_contents() (PHP)
open().read() (Python)
FileInputStream (Java)
File.ReadAllText() (C#)
fs.readFile() (Node.js)

# Database
mysqli_fetch_*(), pg_fetch_*() (PHP) - Second-order SQLi
cursor.fetchone() (Python) - Second-order SQLi
ResultSet.getString() (Java) - Second-order SQLi
```

**Sinks** (Dangerous Operations):
```
# Command Execution
system(), exec(), shell_exec() (PHP)
os.system(), subprocess.Popen() (Python)
Runtime.exec() (Java)
Process.Start() (C#)
child_process.exec() (Node.js)

# SQL Execution
mysqli_query(), pg_query() (PHP)
cursor.execute() (Python)
Statement.execute() (Java)
SqlCommand.ExecuteReader() (C#)

# File Operations
file_put_contents(), fopen() (PHP)
open('w') (Python)
FileOutputStream (Java)
File.WriteAllText() (C#)
fs.writeFile() (Node.js)

# Code Execution
eval(), assert(), include() (PHP)
eval(), exec(), __import__() (Python)
Class.forName() (Java)
Assembly.Load() (C#)
eval(), Function() (JavaScript)

# Deserialization
unserialize() (PHP)
pickle.loads() (Python)
readObject() (Java)
BinaryFormatter.Deserialize() (C#)
JSON.parse() on modified data (JavaScript)
```

### Taint Analysis Methodology

**Step 1: Identify Entry Points**
```bash
# Find all user input points
grep -r "\$_GET\|\$_POST\|\$_REQUEST" .
grep -r "request\\.args\|request\\.form" .
grep -r "getParameter\|getHeader" .
```

**Step 2: Trace Data Flow**
```
User Input → Variable Assignment → Function Call → Sink
$_GET['id'] → $user_id → getUser($user_id) → "SELECT * FROM users WHERE id = $user_id"
```

**Step 3: Check for Sanitization**
```php
// SAFE: Input validated
$id = intval($_GET['id']); // Converted to integer
$query = "SELECT * FROM users WHERE id = " . $id;

// VULNERABLE: No validation
$id = $_GET['id'];
$query = "SELECT * FROM users WHERE id = '" . $id . "'";
```

## Part 3: Vulnerability-Specific Checklists

### SQL Injection

**Quick Grep**:
```bash
# PHP
grep -rn "query\|mysql_query\|mysqli_query\|pg_query" . | grep -v "prepare"

# Python
grep -rn "execute\|executemany" . | grep -v "\\?"

# Java
grep -rn "executeQuery\|executeUpdate" . | grep -v "PreparedStatement"

# C#
grep -rn "ExecuteReader\|ExecuteNonQuery" . | grep -v "Parameters"
```

**Code Patterns**:
```php
// VULNERABLE
$query = "SELECT * FROM users WHERE id = " . $_GET['id'];
$query = "SELECT * FROM users WHERE name = '" . $_GET['name'] . "'";
$query = sprintf("SELECT * FROM users WHERE id = %s", $_GET['id']);

// SAFE
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([$_GET['id']]);
```

### Command Injection

**Quick Grep**:
```bash
grep -rn "system\|exec\|shell_exec\|passthru\|popen\|proc_open" .
grep -rn "os\\.system\|subprocess\\.Popen" .
grep -rn "Runtime\\.exec\|ProcessBuilder" .
grep -rn "Process\\.Start" .
grep -rn "child_process\\.exec" .
```

**Code Patterns**:
```php
// VULNERABLE
system("ping -c 4 " . $_GET['host']);
exec("convert " . $_FILES['image']['tmp_name'] . " output.jpg");

// SAFER (but still validate!)
$host = escapeshellarg($_GET['host']);
system("ping -c 4 " . $host);
```

### Deserialization

**Quick Grep**:
```bash
# PHP
grep -rn "unserialize" .

# Python
grep -rn "pickle\\.loads\|pickle\\.load\|yaml\\.load" .

# Java
grep -rn "readObject\|XMLDecoder\|XStream" .

# C#
grep -rn "BinaryFormatter\|ObjectStateFormatter" .
```

**Code Patterns**:
```php
// VULNERABLE
$data = unserialize($_COOKIE['user_data']);

// Python VULNERABLE
import pickle
user_data = pickle.loads(request.cookies.get('data'))

// Java VULNERABLE
ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(data));
Object obj = ois.readObject();
```

### XXE (XML External Entity)

**Quick Grep**:
```bash
# PHP
grep -rn "simplexml_load\|DOMDocument\|XMLReader" .

# Java
grep -rn "DocumentBuilder\|SAXParser\|XMLStreamReader" .

# C#
grep -rn "XmlDocument\|XmlTextReader" .
```

**Code Patterns**:
```php
// VULNERABLE
$xml = simplexml_load_string($_POST['xml']);

// SAFE
libxml_disable_entity_loader(true);
$xml = simplexml_load_string($_POST['xml'], 'SimpleXMLElement', LIBXML_NOENT);
```

### SSTI (Server-Side Template Injection)

**Quick Grep**:
```bash
# Python
grep -rn "render_template_string\|Template(" .

# PHP
grep -rn "createTemplate\|render" .

# Java
grep -rn "new Template\|template\\.process" .
```

**Code Patterns**:
```python
# VULNERABLE
template = f"Hello {request.args.get('name')}"
return render_template_string(template)

# SAFE
return render_template('hello.html', name=request.args.get('name'))
```

### Path Traversal

**Quick Grep**:
```bash
grep -rn "file_get_contents\|fopen\|readfile\|include\|require" . | grep "\$_"
grep -rn "open(" . | grep "request\\."
grep -rn "FileInputStream\|FileReader" . | grep "getParameter"
```

**Code Patterns**:
```php
// VULNERABLE
$file = $_GET['file'];
include("/var/www/html/" . $file);
// Attack: ?file=../../../../etc/passwd

// SAFER
$file = basename($_GET['file']); // Remove directory components
if (file_exists("/var/www/html/uploads/" . $file)) {
    include("/var/www/html/uploads/" . $file);
}
```

## Part 4: OSWE Exam Quick Wins

### 15-Minute Code Review Strategy

**Phase 1: Grep for Low-Hanging Fruit (5 min)**
```bash
# Command injection
grep -rn "system\|exec" . | head -20

# SQL injection
grep -rn "\$_GET\|\$_POST" . | grep "query\|SELECT" | head -20

# Deserialization
grep -rn "unserialize\|pickle\|readObject" . | head -10

# File operations
grep -rn "file_get_contents\|include" . | grep "\$_" | head -20
```

**Phase 2: Identify Entry Points (5 min)**
```bash
# Find all files handling user input
grep -rn "\$_GET\|\$_POST\|\$_REQUEST\|\$_COOKIE" . | cut -d: -f1 | sort -u

# Find route definitions
grep -rn "@app\\.route\|@RequestMapping\|app\\.get\|app\\.post" .
```

**Phase 3: Trace High-Value Targets (5 min)**
- Admin panels
- File upload handlers
- Search/filter functions
- Report generation
- Authentication/session management

### Common Exam Vulnerability Locations

| Location | Vulnerability Type | Priority |
|----------|-------------------|----------|
| Admin panels | SQL injection, Command injection | HIGH |
| File upload | Path traversal, Command injection | HIGH |
| Search/filter | SQL injection, Second-order SQLi | HIGH |
| User profile | XSS, Second-order SQLi | MEDIUM |
| API endpoints | SQL injection, Deserialization | HIGH |
| Report generation | SSTI, XXE, SQL injection | HIGH |
| Cookie handling | Deserialization, Session fixation | MEDIUM |
| Password reset | IDOR, Auth bypass | MEDIUM |

### File Upload Quick Cheat Sheet (added for OSWE)

**Dangerous functions / patterns**:
- `move_uploaded_file($_FILES[...])`, `$_FILES['x']['name']` without sanitization
- `basename($_FILES['f']['name'])` + direct use (still dangerous extension)
- `pathinfo(..., PATHINFO_EXTENSION)` + weak `in_array`
- `getimagesize()` / `exif_imagetype()` only (bypassable with magic + code)
- .NET: `PostedFile.SaveAs(originalName)`
- Java: `file.transferTo(new File(uploadDir, originalFilename))`

**High-yield grep**:
```bash
grep -rn "move_uploaded_file\|$_FILES\|PostedFile\|MultipartFile\|getOriginalFilename" .
```

**Common bypasses to look for / test**:
- Double extension: `shell.php.jpg`
- Content-Type lie + correct ext
- Magic bytes prefix (GIF89a / JPEG SOI) + .php
- Case: `shell.PHP`
- Path traversal in name or later include of upload path

**See full treatment**: `guides/File-Upload-to-RCE.md` + `poc-examples/file-upload-rce/`


### Critical Files to Review First

**PHP Applications**:
```
config.php          # Database credentials
admin/*.php         # Admin functionality
upload.php          # File upload
search.php          # Search/filter
login.php           # Authentication
```

**Python (Flask/Django)**:
```
views.py            # Route handlers
models.py           # Database models
admin.py            # Admin interface
forms.py            # Form handling
settings.py         # Configuration
```

**Java (Spring)**:
```
*Controller.java    # Route controllers
*Service.java       # Business logic
*Repository.java    # Database access
SecurityConfig.java # Security configuration
application.properties # Configuration
```

**.NET (ASP.NET)**:
```
*.aspx.cs           # Code-behind files
*Controller.cs      # MVC controllers
web.config          # Configuration
Global.asax         # Application events
```

## Part 5: Automated Grep Scripts

### All-in-One Vulnerability Scanner

```bash
#!/bin/bash
# oswe-grep-scan.sh

echo "[+] OSWE Code Review - Quick Scan"
echo ""

echo "[*] Command Injection..."
grep -rn "system\|exec\|shell_exec\|passthru\|popen\|proc_open" . 2>/dev/null | grep -v ".git" | head -10

echo ""
echo "[*] SQL Injection..."
grep -rn "query\|mysql_query\|mysqli_query\|execute" . 2>/dev/null | grep -v "prepare\|.git" | head -10

echo ""
echo "[*] Deserialization..."
grep -rn "unserialize\|pickle\|readObject\|BinaryFormatter" . 2>/dev/null | grep -v ".git" | head -10

echo ""
echo "[*] XXE..."
grep -rn "simplexml_load\|DOMDocument\|DocumentBuilder\|XmlDocument" . 2>/dev/null | grep -v ".git" | head -10

echo ""
echo "[*] SSTI..."
grep -rn "render_template_string\|Template(" . 2>/dev/null | grep -v ".git" | head -10

echo ""
echo "[*] File Operations..."
grep -rn "file_get_contents\|fopen\|include\|require" . 2>/dev/null | grep "\$_" | head -10

echo ""
echo "[+] Scan complete"
```

## Part 6: Second-Order Vulnerability Patterns

### Storage → Execution Flow

**Storage Points** (usually safe with prepared statements):
```php
$stmt = $pdo->prepare("INSERT INTO users (username, bio) VALUES (?, ?)");
$stmt->execute([$username, $bio]); // Payload stored safely
```

**Execution Points** (vulnerable if stored data used unsafely):
```php
// VULNERABLE
$search = $_GET['search'];
$query = "SELECT * FROM users WHERE username = '$search'";
// If $search contains stored SQLi payload → execution

// VULNERABLE
$comment_id = $_GET['id'];
$comment = $db->query("SELECT content FROM comments WHERE id = $comment_id")->fetch();
echo "<div>" . $comment['content'] . "</div>"; // Stored XSS
```

### Quick Identification

```bash
# Find storage (INSERT/UPDATE with prepared statements)
grep -rn "prepare.*INSERT\|prepare.*UPDATE" .

# Find execution (SELECT/DELETE with concatenation)
grep -rn "SELECT\|DELETE" . | grep -v "prepare" | grep "\$"
```

## Part 7: Source Code Recovery Workflow (White-Box Labs)

When source is not provided (very common in AWAE/OSWE targets):

### .NET Recovery
1. Locate assemblies (often in `bin/`, `App_Data/`, or installed app folders).
2. Use **dnSpy** / **ILSpy** (preferred) or `ildasm`.
3. Search for:
   - `Deserialize`, `ObjectStateFormatter`, `XmlSerializer`, `JavaScriptSerializer`, `BinaryFormatter`.
   - Cookie handlers, ViewState usage, `LoadPostData`, custom binders.
   - Dangerous sinks: `Process.Start`, `File.WriteAll`, SQL concatenation.
4. Reconstruct call paths back to HTTP entry points (cookies, form fields, headers, query params).

### Java Recovery
1. Identify the servlet container (Tomcat common). Look for `webapps/ROOT/WEB-INF/`.
2. Key files:
   - `web.xml` → servlet mappings, filters, security constraints.
   - `lib/*.jar` and `classes/` for the app bytecode.
3. Decompile with **jd-gui**, **jadx**, or `cfr`.
4. Map URLs → servlets → service methods.
5. Trace user-controlled data (request params, headers, paths) into dangerous calls:
   - JDBC `Statement` / string concat.
   - `Runtime.exec`, file ops, deserialization.
   - `ObjectInputStream`, `XMLDecoder`, XStream, etc.

### Practical Tips from AWAE Labs
- Start with servlet/endpoint discovery (`web.xml` or route registration).
- Decompile only what you need; focus on the feature under test.
- Rename decompiled variables mentally as you trace (user input → sink).
- Cross-reference with live Burp traffic (match parameter names to source variables).
- For deserialization: identify the exact serializer and expected root type.

See the "Core WEB-300 / OSWE Lab Patterns" section in the Study Roadmap and the manageengine / dotnet PoC notes for concrete source recovery + servlet / cookie handler examples.

## References
- OWASP Code Review Guide: https://owasp.org/www-project-code-review-guide/
- CWE Top 25: https://cwe.mitre.org/top25/
- SANS Secure Coding: https://www.sans.org/posters/secure-coding/
