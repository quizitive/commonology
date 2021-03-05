#!/usr/bin/env bash

# This should source and export all vars in secret_env
set -a
source $HOME/secret_env
set +a

$HOME/.pyenv/versions/commonology/bin/gunicorn --access-logfile - --workers 3 --bind unix:/home/django/commonology/commonologygame.sock project.wsgi:application
