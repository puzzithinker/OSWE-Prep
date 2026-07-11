<?php
// OSWE-LAB: unserialize cookie "data" → EvilClass::__destruct
header("X-Powered-By: PHP/OSWE-LAB-poi");

class EvilClass {
    public $command;
    function __destruct() {
        if (isset($this->command) && $this->command !== "") {
            // VULNERABLE
            system($this->command);
        }
    }
}

echo "<h1>OSWE-LAB · PHP Object Injection</h1>";
echo "<p>Cookie/param <code>data</code> is passed to <code>unserialize()</code>.</p>";
echo "<p>Compatible with generic POP: <code>O:9:\"EvilClass\":1:{s:7:\"command\";s:N:\"CMD\";}</code></p>";

$raw = null;
if (isset($_COOKIE["data"])) {
    $raw = $_COOKIE["data"];
} elseif (isset($_POST["data"])) {
    $raw = $_POST["data"];
} elseif (isset($_GET["data"])) {
    $raw = $_GET["data"];
}

if ($raw !== null && $raw !== "") {
    echo "<pre>Deserializing...</pre>\n";
    echo "<pre>cmd output:\n";
    // force string (cookie may be urldecoded already)
    $obj = @unserialize($raw);
    // if destruct didn't fire yet, trigger explicitly
    if (is_object($obj)) {
        unset($obj);
    }
    echo "</pre>\n<p>Done.</p>";
} else {
    echo "<p>No data provided — set cookie <code>data</code>.</p>";
}

echo "<p>Flag: /flag.txt</p>";
