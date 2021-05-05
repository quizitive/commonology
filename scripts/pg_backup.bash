#!/usr/bin/env bash

set -a
source /etc/profile.d/django_project.sh
set +a

export DAYOFWEEK=$(date +"%a")
FN="$DBNAME"_"$DAYOFWEEK.tar"
pg_dump -h localhost -F t -U postgres $DBNAME > $PG_DUMP_DIR/$FN
echo $FN
# To restore:
# pg_restore --clean --create --no-acl --no-owner -d $DBNAME $DBNAME_$DAYOFWEEK.tar
#
