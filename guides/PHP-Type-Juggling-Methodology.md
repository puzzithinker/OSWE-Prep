# PHP Type Juggling Methodology

**Goal**: Recognize loose comparisons, magic hashes / coercions, and turn them into auth bypass chains for OSWE-style PHP apps.

**Companions**: `notes/ATUTOR-2.2.1-TYPE-JUGGLING.md`, `poc-examples/atutor-type-juggling/`, OWASP “PHP Magic Tricks: Type Juggling”.

---

## 1. Why this matters

PHP’s `==` and `!=` perform **type coercion**. Security checks written as:

```php
if ($user_input == $secret) { /* allow */ }
```

can accept values that are **not** the secret but still compare equal after juggling. This breaks password resets, API tokens, remember-me cookies, and sometimes login.

---

## 2. Core coercion rules (exam-relevant)

### Magic hashes (`0e…`)

Strings that look like scientific notation with only digits after `0e` become float **0** in numeric comparisons:

```php
"0e123" == "0e456";     // true  (0 == 0)
"0e123" == 0;           // true
md5('240610708') == md5('QNKCDZO'); // true — both magic MD5s
```

If both sides of `==` are magic-hash **strings**, comparison succeeds even though strings differ.

### Other useful coercions

| Left | Right | Notes |
|------|-------|-------|
| `"0"` | `false` / `0` | Truthiness pitfalls |
| `"abc"` | `0` | Non-numeric string → 0 in numeric context |
| `"0000"` | `"0"` | Numeric string weirdness |
| Arrays vs strings | | `==` edge cases; `strcmp` array tricks (historical) |

Focus first on **hash/token `==`** — highest exam ROI.

---

## 3. Where to hunt (white-box)

```bash
grep -Rn '==\|!=' --include='*.php' . | grep -iE 'pass|token|hash|md5|sha|confirm|reset|otp|cookie'
grep -Rn 'md5\s*(\|sha1\s*(\|hash\s*(' --include='*.php' .
grep -Rn 'hash_equals\|===' --include='*.php' .   # absences near secrets are smells
```

### High-value code shapes

```php
// reset token
if ($_GET['token'] == $row['token']) { ... }

// strcmp misuse (historical)
if (strcmp($_POST['pass'], $pass) == 0) { ... }

// json_decode without strict types
if ($data['admin'] == true) { ... }  // "true" string / "1" issues
```

### Black-box hints

- Reset links with long hex tokens  
- “Confirm email” with `hash=` parameter  
- APIs comparing HMAC hex with `==`  
- Login with loosely typed JSON bodies (`"admin":1`)

---

## 4. Exploitation patterns

### Pattern A — Both sides magic

If application compares two MD5 hex strings with `==` and you can influence **either** side into a magic hash, auth may succeed.

Examples of known MD5 magic plaintexts (teaching set):

| Plaintext | MD5 |
|-----------|-----|
| `240610708` | `0e462097431906509019562988736854` |
| `QNKCDZO` | `0e830400451993494058024219903391` |
| `s878926199a` | `0e545993274517709034328855841020` |

### Pattern B — Compare to integer 0

```php
if ($_GET['id'] == 0) { ... } // "0e..." or "abc" may juggle
```

### Pattern C — True/false auth flags

JSON/`TRUE`/`"true"`/1 confusion on role flags.

### Pattern D — `switch` / `case` loose compare

`switch` uses loose comparison — surprising case matches.

---

## 5. End-to-end chain (typical)

```text
1. Find loose compare on reset/confirm token
2. Trigger reset for high-value user (admin)
3. Supply magic token / craft state so == succeeds
4. Set password or gain session
5. Use privileged feature → upload/RCE
```

Always plan **step 5** during recon (file manager, plugin, zip).

---

## 6. PoC stages

```text
recon        → version, reset endpoints, param names
trigger      → request reset for victim (if needed)
bypass       → submit juggling payload
authenticate → login with new password / session
escalate     → upload or admin action
verify       → whoami / flag
```

Use session jar; handle multi-step redirects.

---

## 7. PHP version notes

- Behavior of some edge coercions changed over PHP 7/8 (`==` still dangerous for secrets).
- Prefer labs on PHP versions matching target.
- `hash_equals` available modern PHP — absence is a smell in new code; old code often lacks it.

---

## 8. Defenses (findings language)

1. **`hash_equals($a, $b)`** for all secrets (constant-time, no juggling).  
2. Never use `==` on hashes/tokens.  
3. Strict types / validated integers for IDs.  
4. Random tokens ≥ 128 bits; store hashed; single use; expiry.  
5. Unit tests including magic-hash vectors.

---

## 9. OSWE tactics

| Tip | Detail |
|-----|--------|
| Grep first | Faster than fuzzing resets |
| Don’t only memorize one magic string | Explain *why* `0e` works |
| Chain obsession | Bypass without RCE path is incomplete for many machines |
| Script early | Multi-step HTTP is error-prone manually |
| Time box | 45 min to confirm juggling; then escalate |

### Common mistakes

- Using `===` in your mental model while code uses `==`  
- Testing only admin when student reset is enough to learn flow  
- Ignoring encoding (`urlencode` of token)  
- Stopping at session without mapping file write  

---

## 10. Quick reference

```php
// BAD
if ($token == $dbToken) {}

// GOOD
if (hash_equals($dbToken, $token)) {}
```

```text
Hunt: == near md5/sha/token/reset
Verify: behavioral bypass in lab
Escalate: upload / SQLi / admin
```

**Related**: `guides/Chain-Decision-Trees.md`, `guides/File-Upload-to-RCE.md`.
