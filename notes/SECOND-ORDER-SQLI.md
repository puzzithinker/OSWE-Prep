# Second-Order SQLi Case Study

## Environment
**Application**: Custom PHP registration system
**Database**: MySQL 5.7

## Vulnerable Code
```php
// Registration: Input stored without sanitization
$stmt = $db->prepare("INSERT INTO users (username, lastname) VALUES (?, ?)");
$stmt->execute([$username, $lastname]); // $lastname contains SQLi payload

// Admin search: Stored data used in query without escaping
$query = "SELECT * FROM users WHERE lastname = '$search'"; // VULNERABLE
$result = $db->query($query); // Payload executes here!
```

## Chain Outline
1. Register user with payload: `admin' AND SLEEP(5)-- -`
2. Payload stored in database
3. Admin searches for user by lastname
4. Query becomes: SELECT * FROM users WHERE lastname = 'admin' AND SLEEP(5)-- -'
5. Time delay confirms SQLi
6. Escalate to data extraction or RCE

## Findings
**Root Cause**: Stored data treated as trusted, no escaping in secondary query
**Fix**: Parameterize ALL queries, validate stored data before use
