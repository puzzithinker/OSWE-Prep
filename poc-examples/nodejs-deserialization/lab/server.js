// OSWE-LAB: node-serialize cookie deserialization
const http = require("http");
const serialize = require("node-serialize");
const fs = require("fs");

const PORT = 3000;

function parseCookies(header) {
  const out = {};
  if (!header) return out;
  header.split(";").forEach((part) => {
    const i = part.indexOf("=");
    if (i === -1) return;
    const k = part.slice(0, i).trim();
    const v = decodeURIComponent(part.slice(i + 1).trim());
    out[k] = v;
  });
  return out;
}

const server = http.createServer((req, res) => {
  res.setHeader("X-Powered-By", "Express"); // fingerprint for PoC recon
  const cookies = parseCookies(req.headers.cookie);

  if (req.url.startsWith("/health")) {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok", lab: "node-deserial" }));
    return;
  }

  if (cookies.profile) {
    try {
      // VULNERABLE
      const obj = serialize.unserialize(cookies.profile);
      const name = (obj && obj.username) || (obj && obj.rce) || "user";
      res.writeHead(200, { "Content-Type": "text/html" });
      res.end(
        `<h1>OSWE-LAB Node Deserial</h1><p>Hello ${String(name)}</p>` +
          `<p>Flag: read /flag.txt after RCE</p>`
      );
    } catch (e) {
      res.writeHead(500, { "Content-Type": "text/plain" });
      res.end("unserialize error: " + e.message);
    }
    return;
  }

  const benign = serialize.serialize({ username: "guest" });
  res.writeHead(200, {
    "Content-Type": "text/html",
    "Set-Cookie": "profile=" + encodeURIComponent(benign),
  });
  res.end(
    `<h1>OSWE-LAB · node-serialize</h1>
     <p>Cookie <code>profile</code> is unserialized with node-serialize.</p>
     <p>Refresh after setting a malicious profile cookie.</p>`
  );
});

server.listen(PORT, "0.0.0.0", () => {
  console.log("node-deserial lab on", PORT);
});
