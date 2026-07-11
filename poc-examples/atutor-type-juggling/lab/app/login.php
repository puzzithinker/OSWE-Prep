<?php
// OSWE-LAB type juggling teaching app (ATutor-style flow, not real ATutor)
session_start();
header("X-Powered-By: PHP/OSWE-LAB-typejuggling");
?>
<!DOCTYPE html>
<html>
<head><title>ATutor Lab Login</title></head>
<body>
<h1>ATutor OSWE-LAB (teaching)</h1>
<p>Type juggling lab — banner contains <strong>ATutor</strong> for PoC recon.</p>
<?php if (!empty($_SESSION["user"])): ?>
  <p>Logged in as <b><?=htmlspecialchars($_SESSION["user"])?></b>
  role=<?=htmlspecialchars($_SESSION["role"] ?? "")?></p>
  <p><a href="/admin.php">Admin</a> | <a href="/logout.php">Logout</a></p>
<?php else: ?>
<form method="post" action="/login.php">
  <label>User <input name="user"></label>
  <label>Pass <input name="pass" type="password"></label>
  <button>Login</button>
</form>
<p><a href="/register.php">Register</a> | <a href="/reset.php">Password reset</a></p>
<?php endif; ?>
<?php
// Simple users file store
function users_path() { return sys_get_temp_dir() . "/oswe_users.json"; }
function load_users() {
    $p = users_path();
    if (!file_exists($p)) {
        $admin_token = md5("240610708"); // magic hash MD5 — for demo we also store plain
        $users = [
            "admin" => [
                "pass" => "ChangeMeAdmin!",
                "role" => "admin",
                "reset_token" => "0e462097431906509019562988736854", // magic
            ],
        ];
        file_put_contents($p, json_encode($users));
        return $users;
    }
    return json_decode(file_get_contents($p), true);
}
function save_users($u) { file_put_contents(users_path(), json_encode($u)); }

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $users = load_users();
    $user = $_POST["user"] ?? "";
    $pass = $_POST["pass"] ?? "";
    if (isset($users[$user]) && $users[$user]["pass"] === $pass) {
        $_SESSION["user"] = $user;
        $_SESSION["role"] = $users[$user]["role"];
        header("Location: /login.php");
        exit;
    }
    echo "<p style='color:red'>Login failed</p>";
}
?>
</body>
</html>
