#!/usr/bin/env zsh

if [ -z "$COMMONOLOGY_DEV_DIR" ]; then
  echo "You must set the DJANGO_DEV_DIR env var."
  echo "Something like this:"
  echo "export COMMONOLOGY_DEV_DIR=\"$HOME/Documents/dev/commonology\""
  exit
fi

cd $COMMONOLOGY_DEV_DIR/pg_dumps
rsync -avz -e ssh django@commonologygame.com:~/pg_dumps $COMMONOLOGY_DEV_DIR/
fn=`ls -d *(om[1])`
echo $fn
/usr/local/bin/pg_restore --verbose --clean --no-acl --no-owner -d commonology $fn



