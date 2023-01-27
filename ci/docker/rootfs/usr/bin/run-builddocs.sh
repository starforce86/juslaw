#!/bin/sh
echo -e "--- run sphinx build docs ---"
cp /home/www/app/config/settings/local.py.template /home/www/app/config/settings/local.py
DJANGO_SETTINGS_MODULE=config.settings.local sphinx-build -b html docs sphinx-docs
