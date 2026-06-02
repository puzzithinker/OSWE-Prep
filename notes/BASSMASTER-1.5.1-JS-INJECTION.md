# Bassmaster 1.5.1 JavaScript Injection Case Study

## Environment

- Host OS: Kali attacker, Ubuntu/Node target
- App: bassmaster 1.5.1 (npm package, demo batch endpoint)
- Node: v4.x – v8.x era (vulnerable versions)
- Web URL: http://target:8080/
- Key ports: 8080 (or whatever the demo server binds)
- No DB

**Quick lab**:
```bash
npm install bassmaster@1.5.1
node -e 'require("bassmaster").start(8080)'   # or use the packaged demo server
```

See `poc-examples/bassmaster-js-injection/` for a minimal vulnerable server you can run locally.

## Recon

- Entry points: `/batch` (or similar) POST endpoint that accepts an array of requests with `$apply` or similar "code" fields.
- Roles: Usually public/anonymous API.
- Sinks: Server-side `eval`, `new Function`, or `vm.runInThisContext` / `vm.runInNewContext` on data from the batch "requests".

**Black box**: POST a batch with a test payload; observe if math or `process` leaks in responses or side effects.

## Vulnerability Hypothesis

- Suspected class: Server-side JavaScript injection / unsafe dynamic code evaluation in a batching library.
- Data flow: Attacker supplies a "request" descriptor in a batch array → library interprets `$apply` or similar as code to evaluate in Node context → attacker code runs with full Node privileges.
- Preconditions: The library (bassmaster) or similar hand-rolled batcher uses `eval`-family on untrusted request descriptors without isolation.

## Chain Outline

1. Discover the `/batch` (or equivalent) endpoint via directory brute or source.
2. Analyze the expected JSON shape (array of request objects, some with `$apply` or function-like fields).
3. Craft a payload that abuses the evaluation to call `require('child_process').exec(...)`.
4. Deliver via POST to the batch endpoint.
5. Verify via callback (ping, reverse shell, or HTTP exfil of command result).
6. Escalate (read source, env, write files if permitted, etc.).

## Evidence

- Normal batch request vs malicious batch request/response.
- Listener output or command result exfiltrated.
- (If source available) the exact line doing the unsafe evaluation.

## Findings

### Root Cause
Bassmaster's batch handler used a mechanism (in 1.5.1) that effectively allowed code evaluation of attacker-controlled strings in the Node process. The design goal was convenient "apply a transformation", but the implementation trusted the descriptor content.

Similar issues appear in other "safe eval" or template-in-JS libraries when not properly sandboxed (`vm` is hard to lock down correctly).

### Example Injection Shape (High Level)

The vulnerable path accepted something conceptually like:
```json
{
  "requests": [
    { "method": "get", "path": "/profile" },
    { "$apply": "require('child_process').exec('ping -c 4 attacker') ; return {};" }
  ]
}
```

The `$apply` (or equivalent) was passed to an eval-like construct.

See the PoC and Metasploit module for the precise payload that worked against 1.5.1.

### Fix Ideas

- Do not use `eval`, `new Function`, or `vm.runIn*` on any data that can be influenced by API callers.
- If you need dynamic behavior in a batch API, define a strict allow-list of operations and implement them as data-driven handlers, never as code.
- Use `vm` with a completely frozen context + `import` disabled + no access to `require` or `process` if you must support limited expressions.
- Prefer declarative batching (JSON Pointer, GraphQL, etc.) over "execute this snippet".

## OSWE Exam Tips

- API endpoints that take arrays of "requests" or "operations" are high-value for this class of bug.
- Look in package.json + node_modules for "bassmaster", "mathjs", "safe-eval", or custom eval wrappers.
- JS injection often gives you `child_process` immediately — very fast RCE once the vector is found.
- Blind RCE verification is key (the response may not contain output). Use the payload server or DNS callback.
- In white-box Node audits: search for `eval(`, `new Function(`, `vm.runIn`, `require('vm')`.
- Chaining: After initial RCE you often have the full app source + env vars (DB creds, signing secrets) → easy to find secondary issues or pivot.

## References

- Rapid7 / Metasploit module: https://www.rapid7.com/db/modules/exploit/multi/http/bassmaster_js_injection
- Exploit-DB 40689
- `poc-examples/bassmaster-js-injection/` (working PoC + Notes.md with exact payload construction)
- Related: Celestial HTB (different Node deserial but similar "arbitrary code in Node" mindset)
- General Node sandbox escape reading (see also the Node deserial case study)

See the detailed PoC Notes and source in `poc-examples/bassmaster-js-injection/Notes.md` for the exact working request and verification steps.
