web: gunicorn afteryou.wsgi:application --bind 0.0.0.0:$PORT
# Celery workers replaced with Upstash QStash (serverless, no worker process needed!)
# QStash will make HTTP requests to /api/tasks/* endpoints on schedule
