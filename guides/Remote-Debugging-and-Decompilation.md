# Remote Debugging & Decompilation (WEB-300)

Challenge Labs often give a convenient browser IDE attached to the app. **Exam and real white-box work often do not.** Practice recovering source and attaching debuggers yourself.

**Related**: Challenge-Lab-Playbook · Java / .NET methodology guides · Exam-Day-Runbook.

---

## 1. Goals

| Skill | Why |
|-------|-----|
| Decompile Java / .NET | Source not always plain text on disk |
| Attach debugger | Break on sinks, inspect request-bound variables |
| Read stack traces + logs | Confirm SQLi strings, deserial paths |
| Work over SSH only | Slow RDP is common — `grep`/`find`/`less` still work |

---

## 2. Java

### Decompile

```bash
# jd-gui (GUI) or jadx
jadx -d out/ app.war
# or unzip WAR/JAR and jadx on WEB-INF/classes
unzip app.war -d war/
jadx -d src war/WEB-INF/classes
```

Map: `web.xml` / Spring annotations → controllers → sinks.

### Debug ideas (lab)

- Start app with JDWP if you control launch scripts (lab only):  
  `-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005`  
- VS Code / IDEA remote attach to that port  
- Break on `ObjectInputStream.readObject`, JDBC execute, etc.

**Do not** assume exam permits arbitrary JVM flag changes — often you only attach when the environment already exposes debugging, or you rely on static reading + logs.

### Static-first exam workflow

1. Locate WAR/JAR/classes on debug VM  
2. Copy off **only if exam rules allow** (often **you must not** download to host — re-read guide). Prefer reading on the debug host.  
3. `jadx`/`jd-gui` on allowed machine  
4. Grep decompiled sources for sinks  

---

## 3. .NET

### Decompile

- **dnSpy** / **ILSpy** / **dotPeek** on Windows  
- Linux: `ilspycmd` or copy assemblies to Windows analysis box (policy-permitting)

```text
Look for: BinaryFormatter, LosFormatter, TypeNameHandling, SqlCommand concat, Process.Start
```

### Debug

- Visual Studio attach to w3wp / Kestrel process when symbols/source available  
- dnSpy can also debug in some setups  

Machine keys / ViewState: see `guides/DotNet-Deserialization-Guide.md`.

---

## 4. PHP

Usually source is plain text — “decompile” is rare.

### Dynamic insight

- Temporary `error_log` / `var_dump` on **debug** targets only  
- Xdebug attach when lab provides it  
- Enable MySQL general log / Postgres log_statement for SQLi crafting  

```sql
-- MySQL example (lab): SET global general_log = 1;
```

Remove invasive changes before final target runs.

---

## 5. Node.js

- Source often present; also inspect `node_modules` for library sinks  
- `NODE_OPTIONS=--inspect=0.0.0.0:9229` only when you control process start  
- Chrome `chrome://inspect` or VS Code attach  

---

## 6. Without a fancy IDE (SSH-only survival)

```bash
find /var/www /opt /home -name '*.php' 2>/dev/null | head
rg -n "unserialize|mysqli_query|ObjectInputStream|eval\(" /path/to/app
grep -R "password" -n config/ 2>/dev/null | head
```

Copy critical files into your note tool via terminal carefully (exam rules on exfil of source vary — prefer on-box analysis when required).

---

## 7. Prep exercises

1. Take `poc-examples/java-deserialization-commons/lab` jar → jadx → find `readObject`.  
2. Take a .NET teaching lab / Pwnworks challenge → dnSpy.  
3. On any PHP Docker lab → enable SQL log, fire SQLi, read log.  
4. Practice VS Code remote-SSH to a local Docker container once.

---

## 8. Exam constraints (checklist)

- [ ] Re-read what you may install / download / copy  
- [ ] Decompilers available on allowed attack host  
- [ ] Comfortable without browser-based VS Code  
- [ ] Logging tricks practiced on **debug** systems only  
- [ ] Don’t burn hours fighting RDP — switch to SSH tools  

---

## Related

- `guides/Java-Deserialization-Methodology.md`  
- `guides/DotNet-Deserialization-Guide.md`  
- `guides/Code-Review-Checklists.md`  
- `Challenge-Lab-Playbook.md`  
