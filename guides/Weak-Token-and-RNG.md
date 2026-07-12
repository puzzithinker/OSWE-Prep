# Weak Tokens & Predictable RNG

**Why**: First-flag (auth bypass / ATO) paths in white-box labs often abuse reset tokens, invite codes, OTPs, or session IDs generated with **non-cryptographic RNG** or low entropy.

**Related**: Challenge-Lab-Playbook (1st flag) · Type juggling (different class) · sinks cheatsheet.

---

## 1. What to hunt

| Artifact | Risk if weak |
|----------|----------------|
| Password reset token | Account takeover |
| Email confirm / invite | Registration bypass, invite forge |
| OTP / 2FA codes | Auth bypass |
| “Remember me” / API keys | Session steal |
| JWT signing secret | Forge tokens (if discoverable) |
| Coupon / promo codes | Business logic |

---

## 2. White-box greps

```bash
# PHP
rg -n "rand\(|mt_rand\(|uniqid\(|md5\s*\(\s*time|sha1\s*\(\s*time|microtime" --glob '*.php'

# Python
rg -n "random\.|Random\(|uuid\.uuid1|time\.time\(\).*hash" --glob '*.py'
# good: secrets module

# Node
rg -n "Math\.random|crypto\.pseudoRandomBytes" --glob '*.{js,ts}'
# good: crypto.randomBytes

# Java
rg -n "new Random\(|Math\.random" --glob '*.java'
# good: SecureRandom

# .NET
rg -n "new Random\(|RNGCryptoServiceProvider|RandomNumberGenerator" --glob '*.cs'
```

Also trace: **where token is stored** (DB column, email log, file) and **comparison** (`==` vs `hash_equals`).

---

## 3. Exploitation patterns

### Predictable from time

If seed or value is `md5(timestamp)` or `rand()` seeded with time:

1. Note approximate server time (Date header, pages).  
2. Brute a small window offline.  
3. Submit forged reset/confirm.

### Small space OTP

4–6 digit OTP → scripted brute with rate-limit awareness (lab only; exam apps may allow).

### Leak + weak compare

Token in log/email preview + type juggling or SQLi dump.

### Insecure “random” session

If session IDs are sequential or formulaic, forge after observing one sample (rare but classic).

---

## 4. PoC stages

```text
map_token_generation()
sample_tokens()
model_prng_or_space()
forge_and_submit()
session_as_victim()
```

Automate: no manual “guess in browser” for the final script.

---

## 5. Secure patterns (report)

- `secrets` / `SecureRandom` / `crypto.randomBytes` / `RandomNumberGenerator`  
- ≥ 128-bit tokens; single-use; expiry  
- Constant-time compare  
- Rate limit + lockout on OTP  
- Never derive secrets from time alone  

---

## 6. OSWE tactics

- When you see password reset, **read generator code first**.  
- Combine with SQLi: dump token column instead of predicting.  
- Time-box brute force; prefer crypto breaks that complete in seconds.  
