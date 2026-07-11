<?php
session_start();
function users_path() { return sys_get_temp_dir() . "/oswe_users.json"; }
function load_users() {
    $p = users_path();
    if (!file_exists($p)) return [];
    return json_decode(file_get_contents($p), true) ?: [];
}
function save_users($u) { file_put_contents(users_path(), json_encode($u)); }

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $users = load_users();
    if (!$users) {
        // seed admin
        $users["admin"] = [
            "pass" => "ChangeMeAdmin!",
            "role" => "admin",
            "reset_token" => "0e462097431906509019562988736854",
        ];
    }
    $login = $_POST["form_login"] ?? $_POST["user"] ?? "";
    $email = $_POST["form_email"] ?? $_POST["email"] ?? "";
    $pass = $_POST["form_password"] ?? $_POST["password"] ?? "";
    if ($login && $pass) {
        $users[$login] = [
            "pass" => $pass,
            "role" => "student",
            "email" => $email,
            "reset_token" => md5(random_bytes(8)),
        ];
        save_users($users);
        echo "successfully registered — check your email (lab: use reset.php)";
        echo ' <a href="/login.php">login</a>';
        exit;
    }
}
?>
<!DOCTYPE html>
<html><body>
<h1>ATutor Lab Register</h1>
<form method="post">
  <input name="form_login" placeholder="username" required>
  <input name="form_email" placeholder="email">
  <input name="form_password" type="password" placeholder="password" required>
  <input name="form_password_confirm" type="password" placeholder="confirm">
  <input type="hidden" name="form_firstname" value="Test">
  <input type="hidden" name="form_lastname" value="User">
  <input type="hidden" name="website" value="">
  <button name="form_submit" value="Register">Register</button>
</form>
</body></html>
