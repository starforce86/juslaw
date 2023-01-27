#!/bin/bash
/usr/bin/credentials.sh

echo -e "--- run autotests ---"
pytest --create-db -n auto --cache-clear
