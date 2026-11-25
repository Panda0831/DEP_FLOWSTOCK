FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_ENV=prod

WORKDIR /app

RUN groupadd --system flowstock \
    && useradd --system --gid flowstock --home-dir /app flowstock

COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=flowstock:flowstock . .
RUN mkdir -p /app/media /app/staticfiles \
    && chown -R flowstock:flowstock /app/media /app/staticfiles

USER flowstock
EXPOSE 8000

CMD ["sh", "-c", "if [ \"${RUN_MIGRATIONS:-false}\" = \"true\" ]; then python manage.py collectstatic --noinput --settings=config.settings.prod && python manage.py migrate --settings=config.settings.prod || exit $?; fi; exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --access-logfile - --error-logfile - config.wsgi:application"]
