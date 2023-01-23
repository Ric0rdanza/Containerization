FROM debian

RUN apt-get -y update && apt-get -y install nginx

COPY ./html /usr/share/nginx/html

COPY ./default.conf /etc/nginx/sites-available/default

EXPOSE 80/tcp

CMD ["nginx", "-g", "daemon off;"]