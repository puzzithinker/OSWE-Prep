<?php
// Trigger: searches by username but uses lastname unsafely in a second query
header("Content-Type: text/plain");
$host = getenv("DB_HOST") ?: "db";
$db = new mysqli($host, "oswe", "oswe", "oswe");

$search = $_POST["search"] ?? $_GET["search"] ?? "";
$search_esc = $db->real_escape_string($search);

// First query safe-ish
$res = $db->query("SELECT id, username, lastname FROM users WHERE username = '$search_esc'");
if (!$res || $res->num_rows === 0) {
    echo "no user";
    exit;
}
$row = $res->fetch_assoc();
$ln = $row["lastname"];

// VULNERABLE second-order: lastname concatenated into SQL
$sql = "SELECT username, email FROM users WHERE lastname = '$ln' OR username = 'unused'";
// Actually simpler classic: use lastname in LIKE without escape
$sql = "SELECT * FROM users WHERE lastname = '$ln'";
$start = microtime(true);
$r2 = $db->query($sql);
$elapsed = microtime(true) - $start;
echo "query_time_s=" . $elapsed . "\n";
if ($r2) {
    while ($x = $r2->fetch_assoc()) {
        echo $x["username"] . " " . $x["email"] . "\n";
    }
} else {
    echo "sql error: " . $db->error . "\n";
}
