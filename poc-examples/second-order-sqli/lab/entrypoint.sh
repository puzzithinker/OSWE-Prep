#!/bin/bash
set -e
echo "Waiting for MySQL..."
for i in $(seq 1 60); do
  php -r '@new mysqli(getenv("DB_HOST")?: "db", "oswe", "oswe", "oswe") and exit(0); exit(1);' && break
  sleep 2
done
php /var/www/html/init_db.php || true
apache2-foreground
