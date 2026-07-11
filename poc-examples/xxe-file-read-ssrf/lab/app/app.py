"""OSWE-LAB: XXE with lxml (external entities enabled for teaching)."""
from flask import Flask, request, Response
from lxml import etree

app = Flask(__name__)


@app.get("/")
def index():
    return """
    <h1>OSWE-LAB · XXE</h1>
    <p>POST XML to <code>/upload</code> (form field <code>xml</code> or raw body).</p>
    <form method="post" action="/upload">
      <textarea name="xml" rows="10" cols="70"><?xml version="1.0"?>
<!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file:///flag.txt"> ]>
<data>&xxe;</data></textarea><br>
      <button>Parse</button>
    </form>
    """


@app.route("/upload", methods=["POST", "GET"])
def upload():
    xml = request.form.get("xml") or request.args.get("xml") or request.get_data(as_text=True)
    if not xml:
        return "Send XML in field xml or raw body\n", 400
    try:
        # VULNERABLE: resolve entities + external DTD/entities
        parser = etree.XMLParser(resolve_entities=True, no_network=False, load_dtd=True, huge_tree=True)
        root = etree.fromstring(xml.encode() if isinstance(xml, str) else xml, parser=parser)
        text = "".join(root.itertext())
        return Response(text or etree.tostring(root).decode(), mimetype="text/plain")
    except Exception as e:
        return f"XML parse error: {e}\n", 400


@app.get("/health")
def health():
    return {"status": "ok", "lab": "xxe"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
