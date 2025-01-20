#!/bin/sh

fn=`ls -t /pg_dumps/*.tar | head -1`
pg_restore -d $DBNAME --verbose --clean --no-acl --no-owner $fn