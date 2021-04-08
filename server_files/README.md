This whole server_files dir structure does not do anything.
It is just reference material for setting up the server.

***

# Setting up a Digital Ocean Server for Django

Great Reference: [How to Setup Django](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-16-04)

Nearly all of this should work for any Ubuntu server.

We'll use Nginx, Gunicorn, and Django.

Notes: 
1. Wherever I use angle brackets in a command I mean for you to replace it with the appropriate value.  i.e. `<ip address>`, or `<domain name>` should be replaced with your ip address or domain name.
2. As an example I'll use our commonologygame project so you may see commonologygame.com or commonologygame for a database name in this doc.  Replace that with your domain or project.
3. **DO NOT USE** commonologygame anywhere on your server. 


## Get Digital Ocean Ubuntu Droplet
An obvious first step.

- Allocate a Basic 1G/25G Ubuntu Droplet.
  Create a http://digitalocean.com account and allocate an Ubuntu droplet.
  
  Digital Ocean will assign a domain name for the droplet.  
  In the next section I will change it to fit my domain.
 
- Set the DNS A record for for your domain or subdomain for that server. 

  I use http://namecheap.com for domain registaration and DNS services.  
  Other popular choices are http://godaddy.com or http://aws.com.
  
  ```
  A @ <your droplet ip address>
  ```

  Obviously replace <ip address> with the ip address for your droplet.  
  Note, this is a DNS record change and could hours or even days before it works.

  You may want other servers as subdomains.  
  I like to have a second staging server/droplet so I added this A record as well:

  ```
  A staging <your staging droplet ip address>
  ```

  This second staging DNS record use the ip address for my Digital Ocean staging droplet.


- login as root
  ```
  # ssh root@staging.commonologygame.com
  # apt udpate
  # apt upgrade
  ```
- You may want to add your development platform public ssh key to the droplets root account 
  `.ssh/authorized_keys` file so you don't need a password to login.
- Install your favorite editor.
  ```
  # apt install emacs
  ```
- [set hostname](https://www.digitalocean.com/community/questions/how-do-i-change-hostname)

  ```
  # hostnamectl set-hostname staging.commonologygame.com
  ```
  
  Edit `/etc/hosts` and add your domain name to the right of localhost:

  ```
  127.0.0.1 localhost staging.commonologygame.com
  ```
  
  Change `preserve_hostname` in `/etc/cloud/cloud.cfg` is set to true.

  Now execute hostnamectl to finish up:

     ```
     # hostnamectl
     # reboot
     ```

  Log back in with:
  `# ssh root@staging.commonologygame.com`
  
  You should have a nice prompt stating domain name of your server as the prompt.  It may just state the subdomain.
  You can always, safely, use `$ hostname` to see the fully qualified domain name (FQDN).


## ufw (Uncomplicated Firewall)

```
# ufw default deny incoming
# ufw default allow outgoing
# ufw allow ssh
# ufw allow OpenSSH
# ufw enable
```

## Install Software
 
```
  # apt update -y
  # cd /home/django/commonologygame/server_files/
  # xargs -a /packages.txt sudo apt-get install
  # cd /usr/bin
  # ln -s pip3 pip
  # ufw allow "Nginx Full"
  # ufw status
  ```
The output of that status should look like this:

```
$ sudo ufw status
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere                  
OpenSSH                    ALLOW       Anywhere                  
Nginx Full                 ALLOW       Anywhere                  
22/tcp (v6)                ALLOW       Anywhere (v6)             
OpenSSH (v6)               ALLOW       Anywhere (v6)             
Nginx Full (v6)            ALLOW       Anywhere (v6)             

q@staging:~$ 
```

You can visit the server with your browser now to see that it is running Nginx. 
Just put http://staging.commonologygame.com in our browser.  You should see a "Welcome to nginx!" page.
Don't worry yet that it isn't secure.  We'll get an ssl certificate soon to secure it.

## Create user django.

  ```
  $ adduser django
  ```

  Enable django to as sudo user, allow django to run commands as superuser using sudo.

  Add this line to the end of `/etc/sudoers`. You'll have to temporarily change the permissions with 
  `chmod +w /etc/sudoers` and then after editing change it back with `chmod -w /etc/sudoers`.

  `django ALL=(ALL) NOPASSWD:ALL`

  You may want to put your public ssh key in `/home/django/.ssh/authorized_keys` so you can login without a password.

  Now you can logout as root and login again:

  `ssh django@staging.commonologygame.com`

  This way you can organize your project in the q user account and use git commands etc.  
  But if you need to do some superuser operations you have permission.

## Set up pyenv

Reference: [pyenv-installer](https://github.com/pyenv/pyenv-installer)

```
  $ curl https://pyenv.run | bash
```

That command will give you a few lines to add to /home/django/.bashrc` do that.
Then logout and log back in again.

```
  $ pyenv install 3.8.2
  $ pyenv shell 3.8.2
  $ pyenv virtualenv commonology
```


## Make ssh keys

  You'll need a set of ssh keys for github and maybe other things described later.

  ```
  $ ssh-keygen
  ```

  The public key file is `/home/django/.ssh/id_rsa.pub`.
  Copy the contents of your public key for this server to the quizitiveprod github acccount.

That should create `/home/django/.ssh/id_rsa_.pub`, a public key. 


## git clone

Clone your git project in the django account on the server.

```
$ cd
$ git clone git@github.com:quizitive/commonology.git
$ pyenv shell commonology
$ cd commonology
$ pip install -r requirements
$ python manage.py collectstatic --noinput
```

Note: you will need to make sure your project settings.py file has the appropriate files for ALLOWED_HOSTS.


## Create env vars in /home/django/secret_env

I use a file with private environment vars defined.
That file may define the `DJANGO_SECRET` value used in your Django settings.py file.

## Postgres

 
### Create a database:

  ```
  $ sudo -u postgres psql
  
  postgres=# CREATE DATABASE commonology;
  postgres=# CREATE USER postgres with password 'postgres';
  postgres=# ALTER ROLE postgres SET client_encoding TO 'utf8';
  postgres=# ALTER ROLE postgres SET default_transaction_isolation TO 'read committed';
  postgres=# ALTER ROLE postgres SET timezone TO 'UTC';
  postgres=# GRANT ALL PRIVILEGES ON DATABASE commonology TO postgres;
  postgres=# ALTER USER postgres with superuser;
  postgres=# \q
  ```

### Copy production database to staging server (optional).
  You may want to do this if you are building a staging server.

  Add your public ssh key, `/home/django/.ssh/id_rsa_.pub`, to your production server `/home/django/.ssh/authorized_keys` file.

  Now you can use `rsync -avz -e ssh django@commonologygame.com:~/pg_dumps ~/` to copy over postgres dump files.

  You can load the dump into postgres like this:
  ```
  $ pg_restore --verbose --clean --no-acl --no-owner -d commonology ~/pg_dumps/commonology_Mon.tar 
  ```

## Redis

This was installed earlier when Ubuntu packages were installed.  There should  be anything else to do.

## Celery
systemd files for celery

```
# cp /home/django/commonology/server_files/etc/systemd/system/celery.service /etc/systemd/system/
# cp /home/django/commonology/server_files/etc/systemd/system/celerybeat.service /etc/systemd/system/
# mkdir /etc/conf.d
# cp /home/django/commonology/server_files/etc/conf.d/celery /etc/conf.d/
# cp /home/django/commonology/server_files/etc/tmpfiles.d/celery.conf /etc/tmpfiles.d/ 
# systemctl enable celery
# systemctl enable celerybeat
# sudo systemctl daemon-reload
# mkdir /var/log/celery
# chown django:django /var/log/celery
# mkdir /var/run/celery
# chown django:django /var/run/celery
# sudo systemctl restart celery
# sudo systemctl restart celerybeat
```

## GUnicorn

```shell
$ sudo su -
# cd /etc/systemd/system/
# cp /home/django/commonologygame/server_files/etc/systemd/system/gunicorn.service ./
# systemctl start gunicorn
# systemctl enable gunicorn
# exit
$ cd
$ cd commonologygame
$ ls
```

At this point you should see the `commonologygame.sock` file in the ls listing.


## Nginx

Copy site config files from repo.

```shell
$ sudo su 
# cp /home/django/commonology/server_files/etc/nginx/nginx.conf /etc/nginx/
# cp /home/django/commonology/server_files/etc/nginx/sites-available/commonologygame.com /etc/nginx/sites-available/
# cp /home/django/commonology/server_files/etc/nginx/sites-available/commonologygame.com /etc/nginx/sites-available/
# ln -s /etc/nginx/sites-available/commonologygame.com /etc/nginx/sites-enabled/
# ln -s /etc/nginx/sites-available/commonologygame.com /etc/nginx/sites-enabled/
# rm /etc/nginx/sites-enabled/default
```

If this is a staging server and the domain name is `staging.commonologygame.com` rather than just `commonologygame.com`
then edit `/etc/nginix/sites-available/commonologygame.com` and `/etc/nginx/sites-available/commonologygame.com` and 
prefix those domain names with `staging`.

```shell
# systemctl restart nginx
# systemctl restart gunicorn.service 
```

## Get https certificates 

We'll use [letsencrypt](http://letsencrypt.org)
because it is free and works well.

Reference: [certbot install directions](https://certbot.eff.org/lets-encrypt/ubuntufocal-nginx)

```shell
$ sudo snap install core
$ sudo snap refresh core
$ sudo apt update
$ sudo snap install --classic certbot
$ sudo certbot certonly --nginx
```

For some reason this command sometimes adds the appropriate references to
the end of each config file in `/etc/nginx/sites-available/`.  I copied the records
from the ones in our repo.  We should not have to do this.

## Set outbound email using sendgrid.net

### Configure SendGrid.net

Sign into [sendgrid.net](sendgrid.net) and choose Settings -> Sender Authentication.

1. First authenticate domain:
  - When adding the CNAME recs do not include the domain name part of the host field.
  - This will need to verify new DNS CNAME Records.  It may take a few hours before that works.

2. Then verify a single sender.
3. Create API Key (Settings -> API Keys)
4. SMTP:
    - Server: smtp.sendgrid.net
    - Username: apikey
    - Password: <use API KEY given from step 3>
    - Port: 587 (TLS)
  
Note this can be used for Django, described in the next subsection, or most mail clients including GMail.

### Configure Django Sendmail

See `project/settings.py`

### Mailchimp

You need to logon to Mailchimp and set the Webhook URLs for the Audiences as follows.

You need to create a UUID and put it in the secret_env file and use it in the webhook URL.

Set the Mailchimp webhook for production:
https://commonologygame.com/mailchimp_hook/<UUID>

Set the Mailchimp webhook for staging:
https://staging.commonologygame.com/mailchimp_hook/<UUID>

# Try it!