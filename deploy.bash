#!/bin/bash
set -a
source /etc/profile.d/django_project.sh
set +a


export PATH=$PATH:/home/django/.pyenv/bin
export PYENV_VIRTUALENV_DISABLE_PROMPT=1

eval "$(pyenv init -)"
pyenv activate project

cd /home/django/commonology

git checkout master
git pull origin master
BRANCH=master
if [ $# -ge 1 ]; then
  BRANCH=$1
  git fetch origin $BRANCH:$BRANCH
  git checkout $BRANCH
  if [ $HOSTNAME != "commonologygame.com" ]; then
    echo "Updating DB"
    source scripts/pg_update_dev_db.bash
    cd /home/django/commonology
  fi
fi

echo "About to run pycodestyle."
pycodestyle --config=./setup.cfg .
echo $?
if [ $? -eq 0 ]; then
    echo OK
else
    echo "pycodestyle failed."
    exit;
fi


echo "About to run pip install."
cd /home/django/commonology
pip install -q -r requirements.txt
if [ $? -eq 0 ]; then
    echo OK
else
    echo "pip install failed"
fi

python manage.py migrate
python manage.py collectstatic --noinput

echo "About to run Django tests."
python manage.py test
if [ $? -eq 0 ]; then
    echo OK
else
    echo "failed to django tests."
fi

echo "About to restart gunicorn."
sudo systemctl restart gunicorn
if [ $? -eq 0 ]; then
    echo OK
else
    echo "failed to restart gunicorn."
fi

echo "About to restart celery."
sudo systemctl restart celery
if [ $? -eq 0 ]; then
    echo OK
else
    echo "failed to restart celery."
fi

echo "About to restart celeryserial."
sudo systemctl restart celeryserial
if [ $? -eq 0 ]; then
    echo OK
else
    echo "failed to restart celeryserial."
fi

echo "About to restart celerybeat."
sudo systemctl restart celerybeat
if [ $? -eq 0 ]; then
    echo OK
else
    echo "failed to restart celerybeat."
fi

echo "About to restart daphne."
sudo systemctl restart daphne
if [ $? -eq 0 ]; then
    echo OK
else
    echo "failed to restart daphne"
fi