#!/usr/bin/env zsh

SSH_SRC="django@commonologygame.com"
DEV_DIR="$HOME/Documents/dev"
PROJECT="commonology"
PROJECT_DEV_DIR="$DEV_DIR/$PROJECT"

if [ -z "$PROJECT_DEV_DIR" ]; then
  echo "You must set the DJANGO_DEV_DIR env var."
  echo "Something like this:"
  echo "export PROJECT_DEV_DIR=\"$HOME/Documents/dev/commonology\""
  exit
fi


rsync -avz -e ssh $SSH_SRC:~/pg_dumps $PROJECT_DEV_DIR/
cd $PROJECT_DEV_DIR/pg_dumps
fn=`ls -d *(om[1])`
echo $fn
/usr/local/bin/pg_restore --verbose --clean --no-acl --no-owner -d $PROJECT $fn
