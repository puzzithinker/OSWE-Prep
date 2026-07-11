<?php
session_start();
if (empty($_SESSION["user"]) || ($_SESSION["role"] ?? "") !== "admin") {
    http_response_code(403);
    echo "forbidden";
    exit;
}
$dir = __DIR__ . "/uploads/";
if (!is_dir($dir)) mkdir($dir, 0777, true);
if (!isset($_FILES["file"])) { echo "no file"; exit; }
$name = basename($_FILES["file"]["name"]);
move_uploaded_file($_FILES["file"]["tmp_name"], $dir . $name);
echo "OK /uploads/$name\n";
