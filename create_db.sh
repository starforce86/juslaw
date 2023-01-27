#!/bin/bash

# this will ask you for password, use 'manager' - this is our default pass for postgis container
echo "Create new user: jlp_user"
echo "-------------------------------------------------------------------------------"
createuser -U postgres -h postgres -P -s -e  jlp_user

echo
echo "Create new db: jlp_dev"
echo "-------------------------------------------------------------------------------"
createdb -U jlp_user -h postgres  jlp_dev

echo
echo "Giving user standard password 'manager'"
echo "-------------------------------------------------------------------------------"
psql -U postgres -h postgres -c "ALTER USER jlp_user WITH PASSWORD 'manager';"

echo
echo "Grant all privileges to the user on DB "
echo "-------------------------------------------------------------------------------"
psql -U postgres -h postgres -c "GRANT ALL PRIVILEGES ON DATABASE jlp_dev TO jlp_user;"

echo
echo "Installing postgis extension"
echo "-------------------------------------------------------------------------------"
psql -U postgres -h postgres -c "CREATE EXTENSION postgis;" jlp_dev
