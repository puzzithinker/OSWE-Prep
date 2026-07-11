// OSWE-LAB: Bassmaster-style batch endpoint with path eval ($${...})
// Compatible with poc-examples/bassmaster-js-injection/poc.py
const http = require("http");
const { exec } = require("child_process");

const PORT = 8080;

function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = "";
    req.on("data", (c) => (data += c));
    req.on("end", () => resolve(data));
    req.on("error", reject);
  });
}

// Emulate unsafe evaluation of $${expr} inside path strings
function processPath(path) {
  if (typeof path !== "string") return path;
  const m = path.match(/\$\$\{([\s\S]*)\}$/);
  // PoC uses path: `/$${payload}` 
  const m2 = path.match(/\$\$\{([\s\S]*)\}/);
  const expr = m2 ? m2[1] : null;
  if (expr) {
    // VULNERABLE: eval attacker JS
    try {
      // eslint-disable-next-line no-eval
      eval(expr);
    } catch (e) {
      console.error("eval error", e.message);
    }
  }
  return path;
}

const server = http.createServer(async (req, res) => {
  if (req.url === "/" || req.url.startsWith("/?")) {
    res.writeHead(200, { "Content-Type": "text/html" });
    res.end(
      `<h1>OSWE-LAB · Bassmaster-style batch</h1>
       <p>POST JSON to <code>/batch</code> with requests[].path containing <code>$${'{'}...{'}'}</code></p>
       <p>Flag: /flag.txt</p>`
    );
    return;
  }

  if (req.method === "POST" && (req.url === "/batch" || req.url.startsWith("/batch"))) {
    try {
      const raw = await readBody(req);
      const body = raw ? JSON.parse(raw) : {};
      const requests = body.requests || [];
      for (const r of requests) {
        if (r && r.path) processPath(r.path);
      }
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ results: requests.map(() => ({ statusCode: 200 })) }));
    } catch (e) {
      res.writeHead(500, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: e.message }));
    }
    return;
  }

  res.writeHead(404);
  res.end("not found");
});

server.listen(PORT, "0.0.0.0", () => console.log("bassmaster lab", PORT));
