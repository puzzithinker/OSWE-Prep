# Dangerous Sinks Cheatsheet (White-Box First Pass)

**Use**: first 10–20 minutes on a new codebase. Pair with `guides/Code-Review-Checklists.md` and `guides/Chain-Decision-Trees.md`.

For each hit: note **source** (param/cookie/header/file) → **propagation** → **sink** → **impact hypothesis**.

---

## Universal search pack

```bash
# paste and adapt per language
rg -n "eval\(|exec\(|system\(|popen\(|passthru\(|shell_exec\(|Runtime\.getRuntime|Process\.Start|child_process|ObjectInputStream|unserialize|Deserialize|createStatement|executeQuery|innerHTML|document\.write|include\s*\(|require\s*\(|simplexml|DocumentBuilder|pg_sleep|xp_cmdshell|TypeNameHandling|machineKey|ViewState|ND_FUNC|create_function\s*\("
```

---

## PHP

| Sink / pattern | Risk | Next step |
|----------------|------|-----------|
| `unserialize(` | POI / RCE | Map classes, POP, PHAR |
| `include`/`require` + user input | LFI/RFI | Wrappers, upload chain |
| `eval`, `assert`, `create_function` | Code exec | Direct RCE |
| `system`, `exec`, `passthru`, `shell_exec`, backticks | CMDi | Escape/blind |
| `==` / `!=` on hashes/tokens | Type juggling | Magic hashes |
| `preg_replace` `/e` (legacy) | Code exec | Confirm PHP version |
| SQL concat / `mysqli_query($q)` | SQLi | DB dialect RCE path |
| `move_uploaded_file` + weak checks | Upload | Bypass matrix |
| `simplexml_load_*`, `DOMDocument` | XXE | Entity tests |
| `extract(`, `parse_str(` | Variable overwrite | Auth bypass |
| `md5($_GET` comparisons | Weak auth | Juggling / collisions |

```bash
rg -n "unserialize\(|include\s*\(|require\s*\(|eval\(|shell_exec|passthru|system\s*\(|preg_replace|simplexml|==|move_uploaded_file" --glob '*.php'
```

---

## Java

| Sink / pattern | Risk | Next step |
|----------------|------|-----------|
| `ObjectInputStream.readObject` | Deserial RCE | ysoserial + gadgets |
| `XMLDecoder`, `XStream`, `Yaml.load` | Deserial | Gadget research |
| `Runtime.exec`, `ProcessBuilder` | CMDi | Injection |
| `Statement` + string concat | SQLi | Postgres/MySQL RCE |
| `DocumentBuilder` / SAX / Transformer | XXE | Secure features off? |
| JSP `<%=` user data | XSS | Chain if admin |
| `InitialContext.lookup` (JNDI) | Injection | Log4Shell-class (context) |
| Multipart upload to webapps | Upload RCE | Path + JSP |

```bash
rg -n "ObjectInputStream|readObject\(|XMLDecoder|ProcessBuilder|Runtime\.getRuntime|createStatement|executeQuery|DocumentBuilder|SAXParser|XMLInputFactory" --glob '*.{java,xml}'
```

Also map `web.xml` servlet routes.

---

## .NET / ASP.NET

| Sink / pattern | Risk | Next step |
|----------------|------|-----------|
| `BinaryFormatter.Deserialize` | RCE | ysoserial.net |
| `LosFormatter` / `ObjectStateFormatter` | ViewState RCE | machineKey |
| `TypeNameHandling` ≠ None | JSON deserial | Gadgets |
| `SqlCommand` + concat | SQLi | xp_cmdshell if MSSQL |
| `Process.Start` | CMDi | Args injection |
| `__VIEWSTATE` + weak keys | RCE | ysoserial ViewState plugin |
| Cookie personalization deserial | RCE | DNN-class |
| Upload to web root | ASPX shell | Filters |

```bash
rg -n "BinaryFormatter|LosFormatter|ObjectStateFormatter|TypeNameHandling|Process\.Start|SqlCommand|machineKey|Deserialize\(" --glob '*.{cs,config}'
```

---

## Node.js

| Sink / pattern | Risk | Next step |
|----------------|------|-----------|
| `node-serialize` / `unserialize` | IIFE RCE | Cookie/body |
| `eval`, `new Function` | RCE | Direct |
| `vm.runInThisContext` / weak sandbox | Escape | Bassmaster-class |
| `child_process.exec` + user input | CMDi | Injection |
| `res.render` user-controlled template | SSTI | Engine-specific |
| Mongo `$where` / injection | NoSQLi | Auth bypass |
| `innerHTML` in server-rendered only | XSS | If SSR |

```bash
rg -n "eval\(|unserialize|node-serialize|child_process|vm\.run|new Function|\$where|exec\(" --glob '*.{js,ts}'
```

Check `package.json` for risky deps.

---

## SQL / DB features (any language)

| Feature | DB | Impact path |
|---------|-----|-------------|
| Stacked queries | MSSQL, PG, sometimes MySQL | Multi-statement RCE prep |
| `xp_cmdshell` / OLE | MSSQL | Direct RCE |
| `COPY`, `lo_export`, `pg_read_file` | Postgres | File RW → shell |
| `LOAD_FILE`, `INTO OUTFILE` | MySQL | Read/write |
| UDF | MySQL/PG | RCE |
| Second-order | All | Delayed trigger |

---

## Template engines (SSTI)

| Engine | Probe ideas | RCE direction |
|--------|-------------|---------------|
| Jinja2 | `{{7*7}}`, config | MRO / sandbox escape |
| Twig | `{{7*7}}` | `_self` / env |
| Freemarker | `${7*7}` | Execute |
| Velocity | `#set` | Execute |
| Smarty | `{7*7}` | Older pipes |

See `guides/SSTI-Exploitation-Guide.md`.

---

## XML / XXE

| API | Language | Note |
|-----|----------|------|
| DocumentBuilderFactory | Java | Disable DTD |
| XMLReader | Java | |
| simplexml / DOMDocument | PHP | LIBXML flags |
| XmlDocument | .NET | Framework version matters |
| lxml | Python | resolve_entities |

See `guides/XXE-Attack-Vectors.md`.

---

## File upload quick sinks

| Pattern | Risk |
|---------|------|
| Extension blacklist only | Double ext, case, null, alt extensions |
| Client-side checks only | Replay |
| Content-Type trust | Spoof |
| Zip extract | Zip slip |
| Image re-encode only | Polyglot / skip path |

See `guides/File-Upload-to-RCE.md`.

---

## Auth / session

| Pattern | Risk |
|---------|------|
| Loose hash compare | Type juggling |
| Predictable tokens | Account takeover |
| IDOR on user id | Horizontal priv |
| Missing auth on admin script | Direct priv |
| JWT `alg=none` / weak secret | Auth bypass |

---

## 15-minute first-pass workflow

```text
1. Identify language + entrypoints (5 min)
2. Run language grep pack (5 min)
3. Rank top 5 sinks by attacker reachability (3 min)
4. Write 1–2 hypotheses in CASE template (2 min)
5. Manually confirm #1 — stop grepping
```

---

## Mapping sink → repo resource

| Class | Guide / example |
|-------|-----------------|
| Java deserial | `guides/Java-Deserialization-Methodology.md` |
| .NET deserial | `guides/DotNet-Deserialization-Guide.md` |
| PHP POI | `guides/PHP-Deserialization-Patterns.md` |
| Type juggling | `guides/PHP-Type-Juggling-Methodology.md` |
| SQLi | `guides/Advanced-SQLi-Techniques.md` + Blind + Postgres |
| XXE | `guides/XXE-Attack-Vectors.md` |
| SSTI | `guides/SSTI-Exploitation-Guide.md` |
| Upload | `guides/File-Upload-to-RCE.md` |
| XSS chain | `guides/XSS-to-RCE-Chaining.md` |
| LFI | `guides/LFI-to-RCE.md` |
| Node | node + bassmaster PoCs |
