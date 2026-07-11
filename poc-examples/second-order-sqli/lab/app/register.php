<?php
// Stores lastname without filtering — later used in SQL
header("X-Powered-By: PHP/OSWE-LAB-secondorder");
$host = getenv("DB_HOST") ?: "db";

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $db = new mysqli($host, "oswe", "oswe", "oswe");
    $u = $db->real_escape_string($_POST["username"] ?? "");
    $e = $db->real_escape_string($_POST["email"] ?? "");
    $p = $db->real_escape_string($_POST["password"] ?? "");
    // VULNERABLE: lastname stored raw (second-order payload lives here)
    $ln = $_POST["lastname"] ?? "";
    $stmt = $db->prepare("INSERT INTO users (username,email,password,lastname) VALUES (?,?,?,?)");
    $stmt->bind_param("ssss", $u, $e, $p, $ln);
    $stmt->execute();
    http_response_code(201);
    echo "registered";
    exit;
}
?>
<form method="post">
  <input name="username" placeholder="username">
  <input name="email" placeholder="email">
  <input name="password" placeholder="password">
  <input name="lastname" placeholder="lastname">
  <button>Register</button>
</form>
