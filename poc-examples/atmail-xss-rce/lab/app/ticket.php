<?php
// Stored XSS in tickets viewed by admin
$store = sys_get_temp_dir() . "/oswe_tickets.json";
$tickets = file_exists($store) ? json_decode(file_get_contents($store), true) : [];
if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $tickets[] = [
        "from" => $_POST["from"] ?? "user",
        "body" => $_POST["body"] ?? "",
    ];
    file_put_contents($store, json_encode($tickets));
    echo "Ticket saved. Admin will view at /admin.php";
    exit;
}
?>
<form method="post">
  <input name="from" value="attacker@lab">
  <textarea name="body" rows="6" cols="60"><script>/* XSS */</script></textarea>
  <button>Submit ticket</button>
</form>
