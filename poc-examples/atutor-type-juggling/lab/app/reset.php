<?php
// VULNERABLE: loose comparison on reset token
session_start();
function users_path() { return sys_get_temp_dir() . "/oswe_users.json"; }
function load_users() {
    $p = users_path();
    if (!file_exists($p)) {
        $users = [
            "admin" => [
                "pass" => "ChangeMeAdmin!",
                "role" => "admin",
                "reset_token" => "0e462097431906509019562988736854",
            ],
        ];
        file_put_contents($p, json_encode($users));
        return $users;
    }
    return json_decode(file_get_contents($p), true);
}
function save_users($u) { file_put_contents(users_path(), json_encode($u)); }

$msg = "";
if (isset($_GET["user"]) && isset($_GET["token"])) {
    $users = load_users();
    $user = $_GET["user"];
    $token = $_GET["token"];
    if (isset($users[$user])) {
        $db = $users[$user]["reset_token"];
        // VULNERABLE loose compare
        if ($token == $db) {
            $new = $_GET["newpass"] ?? "hacked123";
            $users[$user]["pass"] = $new;
            save_users($users);
            $msg = "Password reset OK for $user → $new (loose == matched)";
        } else {
            $msg = "Token mismatch (strict would also fail)";
        }
    } else {
        $msg = "Unknown user";
    }
}

// Request reset: sets/displays token for lab simplicity
if (isset($_POST["request_user"])) {
    $users = load_users();
    $u = $_POST["request_user"];
    if (isset($users[$u])) {
        // keep existing magic token for admin; others get random md5
        $msg = "Reset token for $u is: " . $users[$u]["reset_token"] . " (lab shows token instead of email)";
    }
}
?>
<!DOCTYPE html>
<html><body>
<h1>ATutor Lab Password Reset</h1>
<p><?=htmlspecialchars($msg)?></p>
<form method="post">
  <input name="request_user" placeholder="username" value="admin">
  <button>Request reset token (lab)</button>
</form>
<hr>
<form method="get">
  <input name="user" value="admin">
  <input name="token" placeholder="token" value="0e830400451993494058024219903391">
  <input name="newpass" value="pwned">
  <button>Reset with token</button>
</form>
<p>Admin stored token is a magic hash. Any other magic hash <code>==</code> compares true in PHP.</p>
<p>Try token <code>0e830400451993494058024219903391</code> (md5 of QNKCDZO).</p>
</body></html>
