// OSWE-LAB: WebSocket message → command execution (no auth)
const http = require("http");
const fs = require("fs");
const { exec } = require("child_process");
const { WebSocketServer } = require("ws");

const PORT = 8080;
const FLAG = fs.existsSync("/flag.txt")
  ? fs.readFileSync("/flag.txt", "utf8").trim()
  : "OSWE{websocket_injection_lab_flag}";

const server = http.createServer((req, res) => {
  if (req.url === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok", lab: "websocket-injection" }));
    return;
  }
  res.writeHead(200, { "Content-Type": "text/html" });
  res.end(`<!DOCTYPE html>
<html><body>
<h1>OSWE-LAB · WebSocket Injection</h1>
<p>Connect to <code>ws://HOST:8116/ws</code> and send JSON messages.</p>
<pre>
{"type":"echo","msg":"hi"}
{"type":"cmd","cmd":"id"}          // VULNERABLE — runs shell
{"type":"flag"}                    // returns flag after any successful cmd or freely for teaching
</pre>
<p>Browser test console:</p>
<pre>
const ws = new WebSocket("ws://"+location.host+"/ws");
ws.onmessage = e => console.log(e.data);
ws.onopen = () => ws.send(JSON.stringify({type:"cmd",cmd:"id"}));
</pre>
<script>
// optional demo page helpers omitted — use CLI websocat/python
</script>
</body></html>`);
});

const wss = new WebSocketServer({ server, path: "/ws" });

wss.on("connection", (ws) => {
  ws.send(JSON.stringify({ hello: "OSWE-LAB websocket", types: ["echo", "cmd", "flag"] }));

  ws.on("message", (data) => {
    let msg;
    try {
      msg = JSON.parse(String(data));
    } catch {
      ws.send(JSON.stringify({ error: "invalid json" }));
      return;
    }

    if (msg.type === "echo") {
      ws.send(JSON.stringify({ type: "echo", msg: msg.msg || "" }));
      return;
    }

    if (msg.type === "flag") {
      ws.send(JSON.stringify({ type: "flag", flag: FLAG }));
      return;
    }

    if (msg.type === "cmd") {
      // VULNERABLE: user-controlled shell command
      const cmd = String(msg.cmd || "id");
      exec(cmd, { timeout: 3000 }, (err, stdout, stderr) => {
        if (err) {
          ws.send(
            JSON.stringify({
              type: "cmd",
              error: err.message,
              stderr: String(stderr || ""),
            })
          );
          return;
        }
        ws.send(
          JSON.stringify({
            type: "cmd",
            cmd,
            stdout: String(stdout),
            flag_hint: "Also send {\"type\":\"flag\"} or cat /flag.txt",
          })
        );
      });
      return;
    }

    ws.send(JSON.stringify({ error: "unknown type" }));
  });
});

server.listen(PORT, "0.0.0.0", () => console.log("websocket-injection lab", PORT));
