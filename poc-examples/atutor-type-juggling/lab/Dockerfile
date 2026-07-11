FROM php:7.4-apache
RUN a2enmod rewrite && sed -i "s/AllowOverride None/AllowOverride All/g" /etc/apache2/apache2.conf
RUN sed -i "s/AllowOverride None/AllowOverride All/g" /etc/apache2/apache2.conf /etc/apache2/sites-available/000-default.conf 2>/dev/null || true
# PHP 7.4 keeps classic loose comparison teaching behavior clear
RUN docker-php-ext-install mysqli pdo pdo_mysql || true
COPY app/ /var/www/html/
RUN mkdir -p /var/www/html/uploads && chmod 777 /var/www/html/uploads \
 && echo "OSWE{type_juggling_lab_flag}" > /flag.txt \
 && echo "OSWE{type_juggling_lab_flag}" > /var/www/html/flag.txt
EXPOSE 80
