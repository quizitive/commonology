#!/usr/bin/env bash

set -a
source /etc/profile.d/django_project.sh
set +a

export DAYOFWEEK=$(date +"%a")
pg_dump -h localhost -F t -U postgres $DBNAME > $PG_DUMP_DIR/"$DBNAME"_"$DAYOFWEEK.tar"

# To restore:
# pg_restore --clean --create --no-acl --no-owner -d $DBNAME $DBNAME_$DAYOFWEEK.tar
