#!/bin/sh
set -eu

python manage.py collectstatic --noinput --settings=config.settings.prod
python manage.py migrate --settings=config.settings.prod

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-1}" \
  --access-logfile - \
  --error-logfile -
