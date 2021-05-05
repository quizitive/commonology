
This file explains how to set up a single developers account on the staging server.
The developer can then use PyCharm on their localhost desktop using ssh in the
background to sync files to the staging server.  We have a couple of convenient scripts
for updating the developers database on the staging server and for remote starting the
the Django runserver.  Each developer has their own account on the staging server
with a postgres database named for the accounts username.  This way all users can
stage new work on the server and run independent servers.



DATABASE_URL=postgres://{user}:{password}@{hostname}:{port}/{database-name}



alias csm="ssh staging.commonologygame.com"
alias c="ssh django@commonologygame.com"
alias cs="ssh django@staging.commonologygame.com"
alias deployprod="ssh django@commonologygame.com /home/django/commonology/deploy.bash"
alias deploy="ssh django@staging.commonologygame.com /home/django/commonology/deploy.bash master"

alias staging_update_ms_db="ssh staging.commonologygame.com bash /home/ms/commonology/scripts/pg_update_dev_db.bash ms"
alias staging_runserver="ssh -t -L8020:localhost:8020 staging.commonologygame.com bash /home/ms/commonology/scripts/run_user_server.bash"
