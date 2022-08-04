import argparse
import os
import sys
import urllib.request


def get_public_ip():
    with urllib.request.urlopen('https://ifconfig.me') as response:
        html = response.read()
        return html.decode().strip()


systemd_config = """[Unit]
    Description=ui-ssh
    After=network.target
    
    [Service]
    User=root
    Group=root
    WorkingDirectory=/usr/local/uissh/backend
    Restart=always
    RestartSec=5
    ExecStart=/usr/local/uissh/backend/venv/bin/gunicorn UISSH.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
    
    [Install]
    WantedBy=multi-user.target"""

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

    os.system('/usr/bin/python3 ./src/nginx/nginx.py')
    os.system('/usr/bin/python3 ./src/certbot/certbot.py')
    os.system('/usr/bin/python3 ./src/osquery/osquery.py')
    os.system('/usr/bin/python3 ./src/php/php.py')

    os.system(f'/usr/bin/python3 ./src/database/mariadb.py --set_root_password={db_password}')

    os.system(f'/usr/bin/python3 ./src/phpmyadmin/phpmyadmin.py --set_root_password={db_password}')

    os.system('bash install_backend.sh')

    program_dir = '/usr/local/uissh/backend'
    cmd = f'{program_dir}/venv/bin/python3 {program_dir}/manage.py createsuperuser --noinput'
    cmd = f'DJANGO_SUPERUSER_PASSWORD={password} DJANGO_SUPERUSER_USERNAME={username} DJANGO_SUPERUSER_EMAIL={email} {cmd}'
    os.system(cmd)

    # Write the database password to the backend config.
    backend_database_password = "/usr/local/uissh/backend/common/config.py"
    with open(backend_database_password, "r") as f:
        data = f.read().replace("*-*-*root_password*-*-*", db_password)

    with open(backend_database_password, "w") as f:
        f.write(data)

    systemd_path = '/lib/systemd/system/ui-ssh.service'

    with open(systemd_path, "w") as f:
        f.write(systemd_config)

    os.system(f'ln -s {systemd_path}  /etc/systemd/system/ui-ssh.service')
    os.system('systemctl enable --now ui-ssh')

    info = f"""
    --------------------------
    db username:root
    db password:{db_password}
    --------------------------
    email:{email}
    username:root
    password:{password}
    --------------------------
    management address：
      - http://{get_public_ip()}:8000/#/
      - https://dev-dash.uissh.com/#/?apiUrl=https://{get_public_ip()}:8000
        (need to enable ssl.)
    phpmyadmin address:
      - http://{get_public_ip()}:8080
    """
    print(info)
