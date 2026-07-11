# Bassmaster-style JS Injection Lab (Docker)

Teaching clone of the batch `$${...}` eval pattern (not the full npm package).

```bash
./labctl.sh up bassmaster
```

- URL: http://127.0.0.1:8105/batch
- Flag: `/flag.txt`

```bash
python3 ../poc.py --target-ip 127.0.0.1 --target-port 8105 --command "id"
# write flag to web-visible place via command if desired
```
