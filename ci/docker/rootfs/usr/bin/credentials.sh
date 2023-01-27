#!/bin/bash

echo -e "--- init credentials for: $APP_ENV ---"

/usr/bin/rattus > /home/www/app/config/settings/${APP_ENV}.py
/usr/bin/rattus \
 -template=/home/www/app/config/google-credentials/credentials.template > /home/www/app/config/google-credentials/credentials.json