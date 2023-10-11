#!/bin/sh
cd ./src

python manage.py migrate
python manage.py collectstatic --no-input --clear

exec "$@"