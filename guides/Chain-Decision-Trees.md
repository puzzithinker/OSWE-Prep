# Chain Decision Trees

Pivot maps for OSWE-style targets. Start at the box that matches what you **already confirmed**, then follow the first viable branch. Time box each branch (~20–30 min).

---

## 0. Master loop

```text
Confirm primitive
  → Amplify impact (data or privilege)
    → Code execution or flag
      → Script + evidence
If stuck → secondary primitive (don't polish dead ends)
```

---

## 1. You found SQL injection

```text
SQLi confirmed
├─ What DB?
│  ├─ MSSQL ──► sysadmin? ──yes──► xp_cmdshell / OLE ──► RCE
│  │                 └─no──► read data → creds/tokens → auth → other RCE
│  ├─ MySQL ──► FILE priv? ──► INTO OUTFILE / LOAD_FILE
│  │              └─ dump hashes → login → upload
│  └─ Postgres ──► superuser/file? ──► COPY / lo_export → webshell
│                    └─ extract → auth → elsewhere
├─ Blind only? ──► binary search extract (see Blind-SQLi guide)
├─ Second-order? ──► find trigger page → then same as above
└─ No RCE path ──► steal session/secrets → IDOR/admin → upload/deserial
```

**Repo**: Advanced SQLi, Postgres guide, MSSQL PoC, ManageEngine notes.

---

## 2. You found file upload

```text
Upload accepted
├─ Can you hit file via HTTP as code?
│  ├─ yes ──► webshell / reverse shell
│  └─ no ──► path wrong? rename? double ext? case? parser diff?
├─ Stored but not executed
│  ├─ LFI/include exists? ──► include upload ──► RCE
│  ├─ Image processor / convert? ──► polyglot / imagetragick-class (time box)
│  └─ Zip extract? ──► zip slip to webroot
└─ Rejected
   └─ Bypass matrix (File-Upload guide) then re-enter tree
```

---

## 3. You found XSS

```text
XSS works
├─ Who views it?
│  ├─ admin / privileged ──► capture admin dangerous action
│  │                           ──► CSRF/session ride via XSS
│  │                           ──► plugin/upload/config write ──► RCE
│  └─ self / low-priv only ──► steal actions still useful?
│                               ├─ CSRF on state change
│                               └─ pivot to other vulns (don't force RCE)
├─ HttpOnly session ──► ride session (don't need cookie theft)
└─ CSP heavy ──► time box bypass; consider alternate chain
```

**Repo**: XSS-to-RCE guide, Atmail case.

---

## 4. You found auth bypass / type juggling / IDOR

```text
Privileged access gained
├─ Map admin features (10 min)
│  ├─ upload / plugin / template ──► RCE
│  ├─ SQLi in admin-only ──► tree #1
│  ├─ deserial / debug ──► tree #5
│  └─ read secrets / SSH keys / flags
└─ No dangerous feature ──► data-only scoring? extract flags; hunt second vuln
```

---

## 5. You found deserialization

```text
Deserial sink
├─ Java ──► gadget on classpath? ──► ysoserial ──► OOB ──► shell
├─ .NET ──► keys/formatter ──► ysoserial.net ──► OOB ──► shell
├─ PHP ──► POP chain / PHAR ──► file ops / CMDi
└─ Node ──► IIFE / eval ──► child_process
Verify with sleep/ping BEFORE reverse shell
If gadget fails ──► alternate chain / delivery channel (cookie vs body vs file)
```

---

## 6. You found XXE

```text
XXE
├─ In-band file read ──► secrets, source, keys, flags
├─ Blind ──► OOB DTD exfil
├─ SSRF ──► metadata / internal admin / secondary deserial
└─ Rare RCE (expect/jar) ──► only if feature present
Use files to enable other trees (machineKey, DB creds, internal URLs)
```

---

## 7. You found SSTI

```text
SSTI confirmed (math probe)
├─ Identify engine
├─ Read config / secrets via objects
└─ Sandbox escape ──► RCE
If sandboxed hard ──► use for disclosure only; pivot
```

---

## 8. You found LFI (read or include)

```text
LFI
├─ include executes PHP? 
│  ├─ yes ──► log/session poison OR include upload ──► RCE
│  └─ read only ──► configs, keys, source → other trees
└─ php://filter ──► source review turbo mode
```

---

## 9. You found command injection

```text
CMDi
├─ In-band output? ──► direct commands / flag
├─ Blind ──► time / OOB DNS / write web file
└─ Filter ──► separators, encoding, $IFS, wildcards (time box)
```

---

## 10. “I have nothing yet” (first 20 min)

```text
Stack fingerprint
  → Dangerous-Sinks-Cheatsheet greps
  → Auth surface map
  → File upload / XML / serialize / SQL params
  → Pick highest reachability sink
  → Manual confirm
  → Enter tree above
```

---

## Time-box table

| Confirmed primitive | Max time before pivot |
|---------------------|------------------------|
| SQLi no RCE yet | 40 min (incl. extract attempt) |
| Upload rejected | 25 min bypasses |
| XSS no admin view | 20 min then other bug |
| Deserial no callback | 30 min gadget/channel switch |
| XXE no OOB egress | 20 min then use other path |

---

## Scripting reminder

Every successful branch ends with:

```text
Manual proof → skeleton stage → non-interactive run → screenshot → report snippet
```

Not: “I’ll script it after the whole chain is perfect.”
