FROM php:8.1-apache
RUN a2enmod rewrite && sed -i "s/AllowOverride None/AllowOverride All/g" /etc/apache2/apache2.conf
RUN sed -i "s/AllowOverride None/AllowOverride All/g" /etc/apache2/apache2.conf /etc/apache2/sites-available/000-default.conf 2>/dev/null || true
RUN docker-php-ext-install mysqli pdo pdo_mysql
COPY app/ /var/www/html/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
EXPOSE 80
