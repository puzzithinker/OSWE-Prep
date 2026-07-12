# Listener / payload hosting (before PoC)

Allowed pattern on many exam setups: start helpers **before** running the non-interactive PoC.

```bash
# Reverse shell
nc -lvnp 4444

# HTTP for OOB / second-stage / XXE DTD
python3 -m http.server 8000
# serve files from a clean directory only
```

PoC should print clear instructions if a listener must already be up, or embed only fire-and-forget callbacks.

**Final grading run**: no Burp proxy; no interactive `input()`.
