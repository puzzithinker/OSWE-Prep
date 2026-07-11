<!DOCTYPE html>
<html><body>
<h1>OSWE-LAB · XSS → Admin → Plugin</h1>
<ul>
  <li><a href="/ticket.php">Open support ticket (stored XSS)</a></li>
  <li><a href="/admin.php">Admin panel</a> (cookie role=admin)</li>
</ul>
<p>Set admin session: <code>document.cookie="role=admin"</code> or use admin login form.</p>
</body></html>
