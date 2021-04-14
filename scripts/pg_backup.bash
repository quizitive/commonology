#!/usr/bin/env bash

export DAYOFWEEK=$(date +"%a")
pg_dump -h localhost -F t $DBNAME > $PG_DUMP_DIR/"$DBNAME"_"$DAYOFWEEK.tar"

# To restore:
# pg_restore --clean --create --no-acl --no-owner -d $DBNAME $DBNAME_$DAYOFWEEK.tar
