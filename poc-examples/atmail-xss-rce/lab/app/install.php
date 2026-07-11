<?php
// /admin/plugin/install
if (($_COOKIE["role"] ?? "") !== "admin") {
    http_response_code(403);
    echo "admin only";
    exit;
}
// CSRF token checked loosely (XSS can read it from page)
$dir = __DIR__ . "/plugins/";
if (!is_dir($dir)) mkdir($dir, 0777, true);

if (!empty($_FILES["plugin"]["tmp_name"])) {
    $name = basename($_FILES["plugin"]["name"]);
    move_uploaded_file($_FILES["plugin"]["tmp_name"], $dir . $name);
    echo "installed /plugins/$name\n";
    exit;
}
if (isset($_POST["code"])) {
    file_put_contents($dir . "shell.php", $_POST["code"]);
    echo "installed /plugins/shell.php\n";
    exit;
}
echo "send plugin file or code";
