#!/usr/bin/env bash
bash 7\
python3 main.py --login_email=root@root.com --db_root_password=root --login_password=root --test=true

if (/usr/local/uissh/backend/venv/bin/python3 /usr/local/uissh/backend/manage.py check); then
  echo 'ok'
  exit 0
else
  echo 'Failed to install backend.'
  exit 1
fi
