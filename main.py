import argparse
import os
import subprocess
import sys
import urllib.request

PUBLIC_IP = None


def bind_domain(_email, _domain):
    cmd = ['certbot', 'certonly', '-n', '--nginx', '--reuse-key', '--agree-tos', '-m', _email, '--fullchain-path',
           f"/etc/letsencrypt/live/{domain}/fullchain.pem", '--key-path',
           f"/etc/letsencrypt/live/{_domain}/privkey.pem",
           '-d', _domain, '-v']

    p = subprocess.run(cmd, capture_output=True)
    if p.returncode == 0:
        os.system(f'cp ./config/backend_ssl.conf /etc/nginx/sites-available/backend_ssl.conf')
        os.system(f'ln -s /etc/nginx/sites-available/backend_ssl.conf /etc/nginx/sites-enabled/backend_ssl.conf')
        os.system(f'cp ./config/phpmyadmin_ssl.conf /etc/nginx/conf.d/phpMyAdmin.conf')
        os.system("sed -i 's/{domain}/dash.uissh.com/g' /etc/nginx/conf.d/phpMyAdmin.conf")
        os.system("sed -i 's/{domain}/dash.uissh.com/g' /etc/nginx/sites-enabled/backend_ssl.conf")
        os.system("systemctl reload nginx")

    return p


def get_public_ip():
    global PUBLIC_IP

    if PUBLIC_IP is None:
        with urllib.request.urlopen('https://ifconfig.me') as response:
            html = response.read()
            PUBLIC_IP = html.decode().strip()
    return PUBLIC_IP


if __name__ == '__main__':
    if not os.geteuid() == 0:
        sys.exit("\nOnly root can run this script\n")
    parser = argparse.ArgumentParser(description="ui-ssh install script.")
    parser.add_argument('--login_email', type=str,
                        help='website management email.')

    parser.add_argument('--login_username', type=str,
                        help='website management username.', default='root')

    parser.add_argument('--login_password', type=str,
                        help='website management password.')
    parser.add_argument('--db_root_password', type=str,
                        help='Setting the root password ensures that nobody can log into the MariaDB'
                             ' root user without the proper authorisation.')

    parser.add_argument('--domain', type=str, default="")

    args = parser.parse_args()
    email = args.login_email
    username = args.login_username
    password = args.login_password
    db_password = args.db_root_password
    domain = args.domain

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
    print("Write the database password to the backend config.")
    sql_path = "config/sync_config.sql"
    with open(sql_path, "r") as f:
        data = f.read().replace("****", db_password)
    with open(sql_path, "w") as f:
        f.write(data)

    cmd = f'sqlite3 /usr/local/uissh/backend/db.sqlite3 < {sql_path}'
    os.system(cmd)

    if domain:
        if bind_domain(email, domain).returncode != 0:
            domain = None

    # Sync CORS_ALLOWED_ORIGINS and CSRF_TRUSTED_ORIGINS settings
    print("Sync CORS_ALLOWED_ORIGINS and CSRF_TRUSTED_ORIGINS settings")
    _env_path = "/usr/local/uissh/backend/.env"
    with open(_env_path, "r") as f:
        new_data = f"https://dash.uissh.com,http://{get_public_ip()}"
        if domain:
            new_data += f',http://{domain},https://{domain}'

        data = f.read().replace("https://dash.uissh.com", new_data)
    with open(_env_path, "w") as f:
        f.write(data)

    systemd_path = '/lib/systemd/system/ui-ssh.service'
    os.system(f'cp ./config/backend.conf /etc/nginx/sites-available/default')
    os.system(f'cp ./config/ui-ssh.service {systemd_path}')

    os.system(f'ln -s {systemd_path}  /etc/systemd/system/ui-ssh.service')
    os.system('systemctl enable --now ui-ssh')
    os.system('systemctl restart nginx')

    if domain:
        management_info = f"""
    management address：
      - http://{get_public_ip()}/#/
      - https://{domain}/#/
      - https://dev-dash.uissh.com/#/?apiUrl=https://{domain} (need to enable ssl.)
    phpmyadmin address:
      - https://{domain}:8080
      """
    else:
        management_info = f"""
    management address：
      - http://{get_public_ip()}/#/
      - https://dev-dash.uissh.com/#/?apiUrl=https://{get_public_ip()} (need to enable ssl.)
    phpmyadmin address:
      - http://{get_public_ip()}:8080
    """

    info = f"""
    --------------------------
    db username:root
    db password:{db_password}
    --------------------------
    email:{email}
    username:root
    password:{password}
    --------------------------
{management_info}
    """
    print(info)
