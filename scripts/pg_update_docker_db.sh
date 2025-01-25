#!/bin/sh

SSH_SRC="django@commonologygame.com"
DEV_DIR="$HOME/Documents/dev"
if [ $HOSTNAME == "staging.commonologygame.com" ]; then
  DEV_DIR="$HOME"
fi
PROJECT="commonology"
PROJECT_DEV_DIR="$DEV_DIR/$PROJECT"


DBNAME=$PROJECT
if [ $# -ge 1 ]; then
  DBNAME=$1
else
  echo "You can use this for dev databases like: pg_update_dev_d.zsh <dbname>"
fi
echo "DBNAME=$DBNAME"

if [ -z "$PROJECT_DEV_DIR" ]; then
  echo "PROJECT_DEV_DIR did not get set properly."
  echo "Check the vars set at the top of this script."
  exit
fi

echo "Running backups on production."
ssh django@commonologygame.com /home/django/commonology/scripts/pg_backup.bash

rsync -avz -e ssh $SSH_SRC:~/pg_dumps $PROJECT_DEV_DIR/
docker compose exec -upostgres db bash \
-c 'pg_restore -d $DBNAME --verbose --clean --no-acl --no-owner $(ls -t /pg_dumps/*.tar | head -1)'
