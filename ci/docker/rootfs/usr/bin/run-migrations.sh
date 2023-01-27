#!/bin/bash
/usr/bin/credentials.sh

echo -e "--- run migrations ---"
python3 manage.py migrate