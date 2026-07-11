FROM php:8.1-apache
RUN a2enmod rewrite && sed -i "s/AllowOverride None/AllowOverride All/g" /etc/apache2/apache2.conf
RUN sed -i "s/AllowOverride None/AllowOverride All/g" /etc/apache2/apache2.conf /etc/apache2/sites-available/000-default.conf 2>/dev/null || true
COPY app/ /var/www/html/
RUN mkdir -p /var/www/html/plugins && chmod 777 /var/www/html/plugins \
 && echo "OSWE{xss_chain_lab_flag}" > /flag.txt \
 && echo "OSWE{xss_chain_lab_flag}" > /var/www/html/flag.txt
EXPOSE 80
