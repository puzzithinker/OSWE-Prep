#!/usr/bin/env bash
# OSWE Docker lab controller
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
COMPOSE=(docker compose -f "$ROOT/docker-compose.yml")
cd "$ROOT"

usage() {
  cat <<'EOF'
Usage: ./labctl.sh <command> [args]

Commands:
  up [service...]     Start labs (default profile). Optional service names.
  up --profile heavy  Start including java-deserial + mssql-sqli
  down                Stop and remove containers
  build [service...]  Build images
  status              docker compose ps
  urls                Print lab URLs
  logs [service]      Tail logs
  smoke               HTTP health checks
  reset               down -v (destroy volumes) then up
EOF
}

urls() {
  cat <<'EOF'
file-upload     http://127.0.0.1:8101
ssti            http://127.0.0.1:8102
xxe             http://127.0.0.1:8103
node-deserial   http://127.0.0.1:8104
bassmaster      http://127.0.0.1:8105
php-poi         http://127.0.0.1:8106
type-juggling   http://127.0.0.1:8107
second-order    http://127.0.0.1:8108
xss-chain       http://127.0.0.1:8109
pg-sqli         http://127.0.0.1:8110
java-deserial   http://127.0.0.1:8111  (profile: heavy)
mssql-sqli      http://127.0.0.1:8112  (profile: heavy)
dotnet-json     http://127.0.0.1:8113
EOF
}

smoke() {
  local ok=0 fail=0
  while read -r name url; do
    [[ -z "${name:-}" ]] && continue
    code=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 2 --max-time 5 "$url" || echo 000)
    if [[ "$code" =~ ^[23] ]]; then
      echo "[+] $name $url → $code"
      ok=$((ok + 1))
    else
      echo "[-] $name $url → $code (is the service up? ./labctl.sh up $name)"
      fail=$((fail + 1))
    fi
  done <<'EOF'
file-upload http://127.0.0.1:8101/
ssti http://127.0.0.1:8102/
xxe http://127.0.0.1:8103/
node-deserial http://127.0.0.1:8104/
bassmaster http://127.0.0.1:8105/
php-poi http://127.0.0.1:8106/
type-juggling http://127.0.0.1:8107/login.php
second-order http://127.0.0.1:8108/
xss-chain http://127.0.0.1:8109/
pg-sqli http://127.0.0.1:8110/
dotnet-json http://127.0.0.1:8113/
EOF
  echo "OK=$ok FAIL=$fail"
}

cmd="${1:-}"
shift || true

case "$cmd" in
  up)
    PROFILE_ARGS=()
    SERVICES=()
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --profile) PROFILE_ARGS+=(--profile "$2"); shift 2 ;;
        *) SERVICES+=("$1"); shift ;;
      esac
    done
    "${COMPOSE[@]}" "${PROFILE_ARGS[@]}" up -d --build "${SERVICES[@]}"
    echo
    urls
    ;;
  down)   "${COMPOSE[@]}" --profile heavy down ;;
  build)  "${COMPOSE[@]}" build "$@" ;;
  status) "${COMPOSE[@]}" ps ;;
  urls)   urls ;;
  logs)   "${COMPOSE[@]}" logs -f --tail=100 "$@" ;;
  smoke)  smoke ;;
  reset)
    "${COMPOSE[@]}" --profile heavy down -v
    "${COMPOSE[@]}" up -d --build
    urls
    ;;
  -h|--help|help|"") usage ;;
  *) echo "Unknown command: $cmd"; usage; exit 1 ;;
esac
