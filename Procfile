web: gunicorn afteryou.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A afteryou worker --loglevel=info
beat: celery -A afteryou beat --loglevel=info