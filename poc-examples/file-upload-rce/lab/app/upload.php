<?php
// OSWE-LAB: intentionally vulnerable upload (blacklist only, trusts client)
header("X-Powered-By: PHP/OSWE-LAB-upload");

$uploadDir = __DIR__ . "/uploads/";
if (!is_dir($uploadDir)) {
    mkdir($uploadDir, 0777, true);
}
@chmod($uploadDir, 0777);

if ($_SERVER["REQUEST_METHOD"] !== "POST") {
    http_response_code(405);
    echo "POST a file field named 'file'";
    exit;
}

if (!isset($_FILES["file"])) {
    http_response_code(400);
    echo "missing file";
    exit;
}

$name = $_FILES["file"]["name"];
$tmp = $_FILES["file"]["tmp_name"];
$ctype = $_FILES["file"]["type"] ?? "";

// Blacklist only pure *.php (single extension)
if (preg_match('/\.php$/i', $name) && substr_count(strtolower($name), '.') === 1) {
    http_response_code(400);
    echo "php extensions blocked";
    exit;
}

$safe = basename($name);
$dest = $uploadDir . $safe;
if (!move_uploaded_file($tmp, $dest)) {
    http_response_code(500);
    echo "upload failed (perms?)\n";
    exit;
}
@chmod($dest, 0644);

header("Content-Type: text/plain");
echo "OK uploaded as /uploads/" . $safe . "\n";
echo "Content-Type was: " . $ctype . "\n";
