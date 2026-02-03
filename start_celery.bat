@echo off
echo Starting Celery worker and beat scheduler...

REM Start Celery worker
start "Celery Worker" cmd /k "celery -A afteryou worker --loglevel=info"

REM Start Celery beat scheduler
start "Celery Beat" cmd /k "celery -A afteryou beat --loglevel=info"

echo Celery worker and beat scheduler started in separate windows.
echo Close those windows to stop the services.
pause
