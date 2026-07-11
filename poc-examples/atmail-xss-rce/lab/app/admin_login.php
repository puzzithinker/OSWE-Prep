<?php
setcookie("role", "admin", time() + 3600, "/");
header("Location: /admin.php");
