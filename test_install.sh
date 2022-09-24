#!/usr/bin/env bash

if (/usr/local/uissh/backend/venv/bin/python3 /usr/local/uissh/backend/manage.py check); then
  echo 'ok'
  exit 0
else
  echo 'Failed to install backend.'
  exit 1
fi
