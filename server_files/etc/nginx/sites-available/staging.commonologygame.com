
# REMEMBER TO UNLINK sites-enabled/default


server {
        listen 80; #  default_server;
        return 301 https://$host$request_uri;
 }

server {
        index index.html index.htm index.nginx-debian.html;

        server_name staging.commonologygame.com;

    	location = /favicon.ico { access_log off; log_not_found off; }
    	location /static/ {
    	    root /home/django/commonology;
    	}

    	location / {
    	    include proxy_params;
    	    proxy_pass http://unix:/home/django/commonology/commonology.sock;
        }

    #listen [::]:443 ssl ipv6only=on; # managed by Certbot
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/staging.commonologygame.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/staging.commonologygame.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}

