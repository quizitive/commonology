export PATH=$PATH:/home/django/.pyenv/bin
export PYENV_VIRTUALENV_DISABLE_PROMPT=1
eval "$(pyenv init -)"
pyenv activate project
cd $HOME/commonology/
pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
if [ $USER == "ms" ]; then
  PORT=8020
else
  PORT=8030
fi
DEBUG=True python manage.py runserver 127.0.0.1:$PORT
