# SSTI Jinja2 Case Study

## Environment
**Application**: Flask 1.1.2 with Jinja2
**Python**: 3.8

## Vulnerable Code
```python
from flask import Flask, request, render_template_string

@app.route('/')
def index():
    name = request.args.get('name', 'World')
    template = f'<h1>Hello {name}!</h1>'  # VULNERABLE
    return render_template_string(template)
```

## Chain Outline
1. Identify parameter reflected in page
2. Test {{7*7}} → returns 49
3. Leak config with {{config}}
4. Enumerate __mro__ subclasses to find Popen
5. Execute command via Popen
6. Achieve RCE

## Findings
**Root Cause**: User input directly embedded in template string
**Fix**: Use render_template() with separate template files, never use render_template_string() with user input
