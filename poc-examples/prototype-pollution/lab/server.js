// OSWE-LAB: Server-side prototype pollution via unsafe deep merge
// POST /api/prefs with JSON that pollutes Object.prototype → admin bypass + flag
const http = require("http");
const fs = require("fs");
const { execSync } = require("child_process");

const PORT = 3000;
const FLAG = fs.existsSync("/flag.txt")
  ? fs.readFileSync("/flag.txt", "utf8").trim()
  : "OSWE{prototype_pollution_lab_flag}";

// Intentionally vulnerable recursive merge (no key filtering)
function deepMerge(target, source) {
  if (!source || typeof source !== "object") return target;
  for (const key of Object.keys(source)) {
    if (source[key] && typeof source[key] === "object" && !Array.isArray(source[key])) {
      if (!target[key] || typeof target[key] !== "object") target[key] = {};
      deepMerge(target[key], source[key]);
    } else {
      target[key] = source[key];
    }
  }
  return target;
}

// App config object — properties may be inherited after pollution
const appConfig = {
  theme: "light",
  notifications: true,
};

function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = "";
    req.on("data", (c) => (data += c));
    req.on("end", () => resolve(data));
    req.on("error", reject);
  });
}

function isAdmin(req) {
  // Cookie role=admin OR polluted isAdmin on any object (e.g. appConfig)
  const cookie = req.headers.cookie || "";
  if (cookie.includes("role=admin")) return true;
  // Vulnerable check: reads property that can be inherited from Object.prototype
  if (appConfig.isAdmin === true || appConfig.isAdmin === "true") return true;
  const empty = {};
  if (empty.isAdmin === true || empty.isAdmin === "true") return true;
  return false;
}

const server = http.createServer(async (req, res) => {
  res.setHeader("X-Powered-By", "OSWE-LAB-PP");

  if (req.url === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok", lab: "prototype-pollution" }));
    return;
  }

  if (req.url === "/" || req.url.startsWith("/?")) {
    res.writeHead(200, { "Content-Type": "text/html" });
    res.end(`<!DOCTYPE html>
<html><body>
<h1>OSWE-LAB · Server-Side Prototype Pollution</h1>
<p>POST JSON preferences to <code>/api/prefs</code>. Server deep-merges into config
<strong>without blocking <code>__proto__</code></strong>.</p>
<p>Admin panel: <a href="/admin">/admin</a> (needs isAdmin via cookie or pollution).</p>
<pre>
# Pollute then hit admin:
curl -s -X POST http://HOST:8114/api/prefs \\
  -H 'Content-Type: application/json' \\
  -d '{"__proto__":{"isAdmin":true}}'
curl -s http://HOST:8114/admin
</pre>
<p>Flag path: admin page after pollution. Also /flag.txt in container.</p>
</body></html>`);
    return;
  }

  if (req.method === "POST" && req.url === "/api/prefs") {
    try {
      const raw = await readBody(req);
      const body = raw ? JSON.parse(raw) : {};
      // VULNERABLE merge of attacker JSON
      deepMerge(appConfig, body);
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          ok: true,
          config: { theme: appConfig.theme, notifications: appConfig.notifications },
          hint: "If you polluted isAdmin, visit /admin",
        })
      );
    } catch (e) {
      res.writeHead(400, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: e.message }));
    }
    return;
  }

  if (req.url === "/admin" || req.url.startsWith("/admin?")) {
    if (!isAdmin(req)) {
      res.writeHead(403, { "Content-Type": "text/plain" });
      res.end("Forbidden — need isAdmin (cookie role=admin or prototype pollution)\n");
      return;
    }
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end(
      `Welcome admin!\nFLAG: ${FLAG}\n` +
        `Optional RCE proof: GET /admin/exec?cmd=id (polluted/admin only)\n`
    );
    return;
  }

  if (req.url.startsWith("/admin/exec")) {
    if (!isAdmin(req)) {
      res.writeHead(403, { "Content-Type": "text/plain" });
      res.end("Forbidden\n");
      return;
    }
    const u = new URL(req.url, "http://x");
    const cmd = u.searchParams.get("cmd") || "id";
    try {
      const out = execSync(cmd, { timeout: 3000, encoding: "utf8" });
      res.writeHead(200, { "Content-Type": "text/plain" });
      res.end(out);
    } catch (e) {
      res.writeHead(500, { "Content-Type": "text/plain" });
      res.end(String(e.stderr || e.message));
    }
    return;
  }

  res.writeHead(404);
  res.end("not found");
});

server.listen(PORT, "0.0.0.0", () => console.log("prototype-pollution lab", PORT));
