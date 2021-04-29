#!/usr/bin/env zsh

SSH_SRC="django@commonologygame.com"
DEV_DIR="$HOME/Documents/dev"
PROJECT="commonology"
PROJECT_DEV_DIR="$DEV_DIR/$PROJECT"

if [ -z "$PROJECT_DEV_DIR" ]; then
  echo "PROJECT_DEV_DIR did not get set properly."
  echo "Check the vars set at the top of this script."
  exit
fi


rsync -avz -e ssh $SSH_SRC:~/pg_dumps $PROJECT_DEV_DIR/
cd $PROJECT_DEV_DIR/pg_dumps
fn=`ls -d *(om[1])`
echo $fn
psql -U postgres -h localhost -c "DROP DATABASE \"$PROJECT\";"
psql -U postgres -h localhost -c "CREATE DATABASE \"$PROJECT\";"
pg_restore --verbose --clean --no-acl --no-owner -h 127.0.0.1 -d $PROJECT $fn
