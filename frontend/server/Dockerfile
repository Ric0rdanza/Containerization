FROM debian

RUN apt-get -y update && apt-get -y install nginx

COPY ./html /var/www/html

COPY ./default.conf /etc/nginx/sites-available/default.conf

EXPOSE 80/tcp

CMD ["nginx", "-g", "daemon off;"]