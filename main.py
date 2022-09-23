import argparse
import os
import subprocess
import sys
import urllib.request

MIRROR_URL = 'https://mirror-cloudflare.uissh.com/'

BACKEND_VERSION = "v0.0.2-alpha"
BACKEND_URL = F"{MIRROR_URL}https://github.com/UISSH/backend/archive/refs/heads/release-{BACKEND_VERSION}.zip"
FRONTEND_VERSION = "v0.0.2-alpha"
FRONTEND_URL = f"{MIRROR_URL}https://github.com/UISSH/frontend/releases/download/{FRONTEND_VERSION}/django_spa.zip"

USER_EMAIL = 'root@root.com'
USERNAME = 'root'
PASSWORD = 'root'
DB_PASSWORD = 'root'
DOMAIN = None
PUBLIC_IP = None
PROJECT_DIR = "/usr/local/uissh"
PYTHON_BIN = f"{PROJECT_DIR}/backend/venv/bin/python3"


def bind_domain():
    cmd = ['certbot', 'certonly', '-n', '--nginx', '--reuse-key', '--agree-tos', '-m', USER_EMAIL, '--fullchain-path',
           f"/etc/letsencrypt/live/{DOMAIN}/fullchain.pem", '--key-path', f"/etc/letsencrypt/live/{DOMAIN}/privkey.pem",
           '-d', DOMAIN, '-v']

    p = subprocess.run(cmd, capture_output=True)
    if p.returncode == 0:
        os.system(f'cp ./config/backend_ssl.conf /etc/nginx/sites-available/backend_ssl.conf')
        os.system(f'ln -s /etc/nginx/sites-available/backend_ssl.conf /etc/nginx/sites-enabled/backend_ssl.conf')
        os.system(f'cp ./config/phpmyadmin_ssl.conf /etc/nginx/conf.d/phpMyAdmin.conf')
        os.system(f"sed -i 's/{{domain}}/{DOMAIN}/g' /etc/nginx/conf.d/phpMyAdmin.conf")
        os.system(f"sed -i 's/{{domain}}/{DOMAIN}/g' /etc/nginx/sites-enabled/backend_ssl.conf")
        os.system("systemctl reload nginx")
    print(p.stdout)
    return p


def get_public_ip():
    global PUBLIC_IP

    if PUBLIC_IP is None:
        with urllib.request.urlopen('https://ifconfig.me') as response:
            html = response.read()
            PUBLIC_IP = html.decode().strip()
    return PUBLIC_IP


def install_backend():
    cmd = f"""
    mkdir -p {PROJECT_DIR};
    cd {PROJECT_DIR} && \
    wget {BACKEND_URL} -O backend.zip && \
    unzip backend.zip > /dev/null && mv backend-release-{BACKEND_VERSION} backend;
    
    cd {PROJECT_DIR}/backend && python3 -m venv venv && \
    {PROJECT_DIR}/backend/venv/bin/pip install -r requirements.txt && \
    cp {PROJECT_DIR}/backend/.env.template {PROJECT_DIR}/backend/.env && \
    {PYTHON_BIN} manage.py makemigrations && \
    {PYTHON_BIN} manage.py migrate && \
    {PYTHON_BIN} manage.py collectstatic --noinput && \

    cd {PROJECT_DIR}/backend/static && \  
    wget {FRONTEND_URL} -O "django_spa.zip" && \
    rm -rf common spa && \
    unzip django_spa.zip > /dev/null && \
    mv spa common
    """
    os.system(cmd)


def install_lnmp():
    os.system('/usr/bin/python3 ./src/nginx/nginx.py')
    os.system('/usr/bin/python3 ./src/certbot/certbot.py')
    os.system('/usr/bin/python3 ./src/osquery/osquery.py')
    os.system('/usr/bin/python3 ./src/php/php.py')
    os.system(f'/usr/bin/python3 ./src/database/mariadb.py --set_root_password={DB_PASSWORD}')
    os.system(f'/usr/bin/python3 ./src/phpmyadmin/phpmyadmin.py --set_root_password={DB_PASSWORD}')


def init_backend_settings():
    global DOMAIN
    cmd = f'{PYTHON_BIN} {PROJECT_DIR}/backend/manage.py createsuperuser --noinput'
    cmd = f'DJANGO_SUPERUSER_PASSWORD={PASSWORD} DJANGO_SUPERUSER_USERNAME={USERNAME} DJANGO_SUPERUSER_EMAIL={USER_EMAIL} {cmd}'
    os.system(cmd)

    # Write the database password to the backend config.
    print("Write the database password to the backend config.")
    sql_path = "config/sync_config.sql"
    with open(sql_path, "r") as f:
        data = f.read().replace("****", DB_PASSWORD)
    with open(sql_path, "w") as f:
        f.write(data)

    cmd = f'sqlite3 /usr/local/uissh/backend/db.sqlite3 < {sql_path}'
    os.system(cmd)

    if DOMAIN:
        if bind_domain().returncode != 0:
            DOMAIN = None

    # Sync CORS_ALLOWED_ORIGINS and CSRF_TRUSTED_ORIGINS settings
    print("Sync CORS_ALLOWED_ORIGINS and CSRF_TRUSTED_ORIGINS settings")
    _env_path = "/usr/local/uissh/backend/.env"
    with open(_env_path, "r") as f:
        new_data = f"https://dash.uissh.com,http://{get_public_ip()}"
        if DOMAIN:
            new_data += f',http://{DOMAIN},https://{DOMAIN}'

        data = f.read().replace("https://dash.uissh.com", new_data)

    if DOMAIN:
        data = data.replace("WEBSITE_ADDRESS=", f"WEBSITE_ADDRESS={DOMAIN}")

    with open(_env_path, "w") as f:
        f.write(data)

    systemd_path = '/lib/systemd/system/ui-ssh.service'
    os.system(f'cp ./config/backend.conf /etc/nginx/sites-available/default')
    os.system(f'cp ./config/ui-ssh.service {systemd_path}')

    os.system(f'ln -s {systemd_path}  /etc/systemd/system/ui-ssh.service')
    os.system('systemctl enable --now ui-ssh')
    os.system('systemctl restart nginx')


def print_info():
    if DOMAIN:
        management_info = f"""
        management address：
          - http://{get_public_ip()}/#/
          - https://{DOMAIN}/#/
          - https://dev-dash.uissh.com/#/?apiUrl=https://{DOMAIN} (need to enable ssl.)
        phpmyadmin address:
          - https://{DOMAIN}:8080
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
        db password:{DB_PASSWORD}
        --------------------------
        email:{USER_EMAIL}
        username:root
        password:{PASSWORD}
        --------------------------
    {management_info}
        """
    print(info)


if __name__ == '__main__':

    if not os.geteuid() == 0:
        sys.exit("\nOnly root can run this script\n")

    parser = argparse.ArgumentParser(description="ui-ssh install script.")
    parser.add_argument('--login_email', type=str, help='website management email.')

    parser.add_argument('--login_username', type=str, help='website management username.', default='root')

    parser.add_argument('--login_password', type=str, help='website management password.')
    parser.add_argument('--db_root_password', type=str,
                        help='Setting the root password ensures that nobody can log into the MariaDB'
                             ' root user without the proper authorisation.')

    parser.add_argument('--domain', type=str, default="")

    args = parser.parse_args()

    USER_EMAIL = args.login_email
    USERNAME = args.login_username
    PASSWORD = args.login_password
    DB_PASSWORD = args.db_root_password
    DOMAIN = args.domain

    install_lnmp()
    install_backend()
    init_backend_settings()
    print_info()
