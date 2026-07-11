<?php
session_start();
if (empty($_SESSION["user"]) || ($_SESSION["role"] ?? "") !== "admin") {
    http_response_code(403);
    echo "Admin only. Login as admin first.";
    exit;
}
?>
<!DOCTYPE html>
<html><body>
<h1>ATutor Lab Admin</h1>
<p>Welcome admin. Upload a PHP shell:</p>
<form action="/upload.php" method="post" enctype="multipart/form-data">
  <input type="file" name="file">
  <button>Upload</button>
</form>
</body></html>
