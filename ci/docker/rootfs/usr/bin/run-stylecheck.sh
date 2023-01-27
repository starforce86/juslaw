#!/bin/bash
echo -e "--- run isort check ---"
isort apps libs provision --check-only
echo -e "--- run flake8 check ---"
flake8 apps libs provision
