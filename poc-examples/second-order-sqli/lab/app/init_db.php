<?php
$host = getenv("DB_HOST") ?: "db";
$db = new mysqli($host, "oswe", "oswe", "oswe");
if ($db->connect_error) {
    fwrite(STDERR, $db->connect_error);
    exit(1);
}
$db->query("CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(64),
  email VARCHAR(128),
  password VARCHAR(128),
  lastname VARCHAR(256)
)");
$db->query("DELETE FROM users");
$db->query("INSERT INTO users (username,email,password,lastname) VALUES
 ('admin','admin@lab.local','adminpass','Administrator')");
echo "db ready\n";
