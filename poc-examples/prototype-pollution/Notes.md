# Prototype Pollution — Case Notes

## Docker lab

Preferred setup: `cd labs && ./labctl.sh up prototype-pollution`  
See [`lab/README.md`](lab/README.md) and [`labs/README.md`](../../labs/README.md).

---

## Environment

- App: OSWE-LAB Node deep-merge teaching server
- URL: http://127.0.0.1:8114
- Flag: `/flag.txt` → also printed on `/admin` after pollution

## Vulnerability hypothesis

- Class: Server-side prototype pollution (CWE-1321-class)
- Data flow: JSON body → recursive merge → `Object.prototype.isAdmin` → auth check
- Impact: Admin panel + optional command exec

## Chain outline

1. POST polluted prefs  
2. GET /admin → flag  
3. Optional GET /admin/exec?cmd=

## Findings

- Root cause: unfiltered deep merge of attacker keys including `__proto__`
- Fix: block `__proto__`/`constructor`/`prototype`; allow-list keys; use `Map`/`Object.create(null)`

## Methodology

- `guides/Prototype-Pollution-Methodology.md`
