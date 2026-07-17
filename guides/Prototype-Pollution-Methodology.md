# Prototype Pollution Methodology (OSWE-relevant)

**Why it matters (2025–2026)**: WEB-300 includes server-side prototype pollution (often Node) chained to template engines / dangerous option objects → impact beyond “just a JS oddity.” Multiple recent reviews call this module standout.

**Companions**: Docker lab `prototype-pollution` (:8114) · PortSwigger PP labs · SSTI guide · Challenge-Lab-Playbook · sinks cheatsheet (Node).

---

## 1. Concept

In JavaScript, objects inherit from `Object.prototype` (or other prototypes). If an application **merges untrusted JSON** into an object without blocking `__proto__` / `constructor.prototype`, an attacker can define properties that later code treats as trusted configuration.

```js
// Conceptual anti-pattern
deepMerge(target, userControlledObject);
// later
if (options.isAdmin) { ... }  // polluted
// or template engine / child_process options polluted
```

---

## 2. Client-side vs server-side

| | Client-side PP | Server-side PP |
|--|----------------|----------------|
| Where | Browser JS | Node backend merge/clone |
| Typical impact | XSS gadgets, client logic bypass | Auth bypass, RCE via polluted opts |
| OSWE emphasis | Useful context | **Higher exam relevance** when server-side |

---

## 3. White-box hunt

```bash
# Node / frontend bundles (where source available)
rg -n "__proto__|prototype|merge\(|extend\(|defaultsDeep|lodash\.merge|Object\.assign|JSON\.parse" --glob '*.{js,ts}'
```

Look for:

- Recursive merge of request body / query  
- `JSON.parse` then for-in copy without key allow-list  
- Libraries: lodash `merge`, jQuery `extend`, custom `deepCopy`  

### Dangerous follow-on sinks

- Template engines (Pug, Handlebars, EJS options)  
- `child_process` / sandbox options  
- Auth middleware reading config from objects  
- Serialization that rehydrates polluted structures  

---

## 4. Black-box probes (high level)

1. Send JSON body with nested `__proto__` or `constructor.prototype` keys (where content-type is JSON).  
2. Observe behavioral change: new properties on unrelated objects, error messages, feature flags.  
3. Prefer **impact** over alert-style client demos when server-side.

Exact payloads evolve with engine versions — use PortSwigger labs and current academy cheatsheets; keep working payloads in your field manual.

---

## 5. Chaining mindset (exam-style)

```text
Find merge of user JSON
  → pollute property consumed by privileged logic
    → auth bypass / feature unlock  (1st flag class)
  OR pollute template / exec options
    → RCE / file read              (2nd flag class)
```

Document: which property, which consumer, proof request, then script it.

---

## 6. PortSwigger practice track

Complete and **script** where possible:

- Client-side prototype pollution (DOM XSS gadgets)  
- Server-side prototype pollution  
- Privilege escalation via PP  
- Any academy labs tagged prototype pollution  

Tracker: [PortSwigger-Lab-Tracker.md](../PortSwigger-Lab-Tracker.md).

---

## 7. Defenses (report language)

- Block `__proto__`, `constructor`, `prototype` keys on merge  
- Use `Object.create(null)` / `Map` for dictionaries  
- Prefer structured cloning with allow-lists  
- Keep template/exec options on immutable defaults  
- Update vulnerable merge libraries  

---

## 8. OSWE tactics

- Don’t stop at “pollution works” — find the **consumer**.  
- Node `package.json` + merge utilities = high-priority greps.  
- Time-box gadget research; pivot to other sinks if no consumer in 30 min.  
- Script the merge request + verification (property reflected or behavior change).  

**Related**: `guides/SSTI-Exploitation-Guide.md`, `guides/XSS-to-RCE-Chaining.md`, Node deserial labs (different class, same “user JSON is dangerous” instinct).
