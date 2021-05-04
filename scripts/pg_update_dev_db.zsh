#!/usr/bin/env zsh

SSH_SRC="django@commonologygame.com"
DEV_DIR="$HOME/Documents/dev"
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

ssh django@commonologygame.com /home/django/commonology/scripts/pg_backup.bash

rsync -avz -e ssh $SSH_SRC:~/pg_dumps $PROJECT_DEV_DIR/
cd $PROJECT_DEV_DIR/pg_dumps
fn=`ls -d *(om[1])`
echo $fn
psql -U postgres -h localhost -c "DROP DATABASE \"$DBNAME\";"
psql -U postgres -h localhost -c "CREATE DATABASE \"$DBNAME\";"
pg_restore --verbose --clean --no-acl --no-owner -h 127.0.0.1 -d $DBNAME $fn
