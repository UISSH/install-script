python3 main.py --login_email=root@root.com --db_root_password=root --login_password=root --test=true

if (systemctl is-active -q ui-ssh); then
  echo 'ok'
  exit 0
else
  echo 'Failed to install backend.'
  exit 1
fi
