#!/bin/bash

### Generate robots.txt
echo "Configure environment: $APP_ENV"
case $APP_ENV in
    development|staging)
        echo -e "User-agent: *\nDisallow: /" > /home/www/app/robots.txt
        ;;
    production)
        ;;
esac

echo "Update credentials"
/bin/bash /usr/bin/credentials.sh

echo "Collect static"
# update CSS/JS in static folder
python manage.py collectstatic --noinput

# Store the build date and release version
echo `date` >> /home/www/builds
echo "__builddate__ = '`date`'" >> /home/www/app/__version__.py

case $APP_ENV in
    development|staging)
        ### Starting supervisord services
        echo "Starting Celery worker..."
        supervisorctl start celery_worker

        echo "Starting Celery beat..."
        supervisorctl start celery_beat

        echo "Starting NGINX..."
        supervisorctl start nginx

        echo "Starting UWSGI..."
        supervisorctl start api
        ;;
    production)
        case $WORKER_ENV in
            celery)
                ### Starting supervisord services
                echo "Starting Celery worker..."
                supervisorctl start celery_worker

                echo "Starting Celery beat..."
                supervisorctl start celery_beat
                ;;
            api)
                echo "Starting NGINX..."
                supervisorctl start nginx

                echo "Starting UWSGI..."
                supervisorctl start api
                ;;
        esac
        ;;
esac

python manage.py migrate

echo "Exiting bootstrap script"
exit 0
