"""OSWE-LAB: intentionally vulnerable Jinja2 SSTI."""
from flask import Flask, request, render_template_string

app = Flask(__name__)

INDEX = """
<!doctype html>
<html><head><title>OSWE-LAB SSTI</title></head>
<body>
<h1>OSWE-LAB · Jinja2 SSTI</h1>
<p>Greeting uses <code>render_template_string</code> on user input (vulnerable).</p>
<form method="get" action="/">
  <label>Name: <input name="name" value="{{ name }}"></label>
  <button>Go</button>
</form>
<p>Hello {{ name }}</p>
<pre>Try: {{7*7}} then classic Jinja2 RCE payloads</pre>
<p>Flag: /flag.txt on container filesystem</p>
</body></html>
"""


@app.get("/")
def index():
    name = request.args.get("name", "guest")
    # VULNERABLE: user-controlled string is compiled as a Jinja2 template
    return render_template_string(
        """<!doctype html><html><body>
        <h1>OSWE-LAB · Jinja2 SSTI</h1>
        <p>Param <code>name</code> is rendered unsafely.</p>
        <form method="get" action="/"><input name="name"><button>Go</button></form>
        <p>Hello """
        + name
        + """</p>
        <p>Flag path: /flag.txt</p>
        </body></html>"""
    )


@app.get("/health")
def health():
    return {"status": "ok", "lab": "ssti"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
