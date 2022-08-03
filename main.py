import argparse
import os
import sys

systemd_config = """
[Unit]
Description=ui-ssh
After=network.target

[Service]
User=root
Group=www
WorkingDirectory=/usr/local/uissh/backend
Restart=always
RestartSec=5
ExecStart=/usr/local/uissh/backend/venv/bin/gunicorn UISSH.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

[Install]
WantedBy=multi-user.target

"""

if __name__ == '__main__':
    if not os.geteuid() == 0:
        sys.exit("\nOnly root can run this script\n")
    parser = argparse.ArgumentParser(description="ui-ssh install script.")
    parser.add_argument('--set_login_username', type=str,
                        help='website management username.', default='root')
    parser.add_argument('--set_login_email', type=str,
                        help='website management email.')
    parser.add_argument('--set_login_password', type=str,
                        help='website management password.')
    parser.add_argument('--set_db_root_password', type=str,
                        help='Setting the root password ensures that nobody can log into the MariaDB'
                             ' root user without the proper authorisation.')
    args = parser.parse_args()

    email = args.set_login_email
    username = args.set_login_username
    password = args.set_login_password
    db_password = args.set_db_root_password

    os.system('bash install_backend.sh')

    os.system(f'DJANGO_SUPERUSER_PASSWORD={password} '
              f'DJANGO_SUPERUSER_USERNAME={username} '
              f'DJANGO_SUPERUSER_EMAIL={email}'
              f' ./venv/bin/python3 manage.py createsuperuser --noinput')

    os.system('/usr/bin/python3 .src/nginx/nginx.py')
    os.system('/usr/bin/python3 .src/certbot/certbot.py')
    os.system('/usr/bin/python3 .src/osquery/osquery.py')
    os.system('/usr/bin/python3 .src/php/php.py')

    os.system(f'/usr/bin/python3 .src/database/mariadb.py --set_root_password={db_password}')

    os.system(f'/usr/bin/python3 .src/phpmyadmin/phpmyadmin.py --set_root_password={db_password}')

    systemd_path = 'etc/systemd/system/multi-user.target.wants/ui-ssh.service'

    with open(systemd_config,"w") as f:
        f.write(systemd_config)

    os.system(f'ln -s {systemd_path} /lib/systemd/system/ui-ssh.service')
    os.system('systemctl enable --now ui-ssh')

    info = f"""
--------------------------
db username:root
db password:{db_password}
--------------------------
email:{email}
username:root
password:{password}
"""
    print(info)
