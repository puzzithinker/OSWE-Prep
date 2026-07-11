<!DOCTYPE html>
<html>
<head><title>OSWE-LAB File Upload</title></head>
<body>
<h1>OSWE-LAB · File Upload</h1>
<p>Intentionally weak upload filter for practice. Source: <a href="/upload.php.txt">upload.php.txt</a></p>
<form action="/upload.php" method="post" enctype="multipart/form-data">
  <input type="file" name="file" required>
  <button type="submit">Upload</button>
</form>
<p>Uploads land under <code>/uploads/</code>. Flag in <code>/flag.txt</code> (container) and <code>/flag.txt</code> via web if RCE.</p>
</body>
</html>
