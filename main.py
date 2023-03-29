import argparse
import os
import subprocess
import sys
import urllib.request

MIRROR_URL = 'https://mirror-cloudflare.uissh.com/'
TEST_FLAG = False
BACKEND_VERSION = "v0.0.4-alpha"
BACKEND_URL = f"{MIRROR_URL}https://github.com/UISSH/backend/archive/refs/tags/{BACKEND_VERSION}.zip"
FRONTEND_VERSION = "v0.0.16"
FRONTEND_URL = f"{MIRROR_URL}https://github.com/UISSH/react-frontend/releases/download/{FRONTEND_VERSION}/django_spa.zip"

USER_EMAIL = 'root@root.com'
USERNAME = 'root'
PASSWORD = 'root'
DB_PASSWORD = 'root'
DOMAIN = None
PUBLIC_IP = None
PROJECT_DIR = "/usr/local/uissh"
BACKEND_DIR = f"{PROJECT_DIR}/backend"
PYTHON_BIN = f"{PROJECT_DIR}/backend/venv/bin/python3"
PYTHON_PIP = f"{PROJECT_DIR}/backend/venv/bin/pip"


def cmd(_cmd, msg=None, ignore=False):
    if msg:
        print(msg)
    ret = os.system(_cmd)
    if ignore is False and ret != 0:
        print(f"{_cmd} failed")
        exit(1)


def bind_domain():
    _cmd_list = ['certbot', 'certonly', '-n', '--nginx', '--reuse-key', '--agree-tos', '-m', USER_EMAIL,
                 '--fullchain-path', f"/etc/letsencrypt/live/{DOMAIN}/fullchain.pem", '--key-path',
                 f"/etc/letsencrypt/live/{DOMAIN}/privkey.pem", '-d', DOMAIN, '-v']

    if TEST_FLAG:
        _cmd_list = ['echo', 'test']
        p = subprocess.run(_cmd_list, capture_output=True)
    else:
        p = subprocess.run(_cmd_list, capture_output=True)
        print("================================")
        if p.returncode == 0:
            cmd(f'cp ./config/backend_ssl.conf /etc/nginx/sites-available/backend_ssl.conf')
            cmd(f'ln -s /etc/nginx/sites-available/backend_ssl.conf /etc/nginx/sites-enabled/backend_ssl.conf',
                ignore=True)
            cmd(f'cp ./config/phpmyadmin_ssl.conf /etc/nginx/conf.d/phpMyAdmin.conf')
            cmd(f"sed -i 's/{{domain}}/{DOMAIN}/g' /etc/nginx/conf.d/phpMyAdmin.conf")
            cmd(f"sed -i 's/{{domain}}/{DOMAIN}/g' /etc/nginx/sites-enabled/backend_ssl.conf")
            cmd("systemctl reload nginx")
            print(p.stdout)
        else:
            if p.stderr:
                print(p.stderr)
        print("================================")
    return p


def get_public_ip():
    global PUBLIC_IP

    if PUBLIC_IP is None:
        with urllib.request.urlopen('https://ifconfig.me') as response:
            html = response.read()
            PUBLIC_IP = html.decode().strip()
    return PUBLIC_IP


def install_backend():
    # download & install backend
    cmd(f'mkdir -p {BACKEND_DIR}')
    cmd(f'cd {PROJECT_DIR} && wget -q {BACKEND_URL} -O  backend.zip && rm -rf backend-* && '
        f'unzip backend.zip > /dev/null && cp -r backend-{BACKEND_VERSION.replace("v","")}/. backend/',
        'Download & install backend...')
    cmd(f'cd {PROJECT_DIR}/backend && python3 -m venv venv ',
        'Install virtual environment...')
    cmd(f'{PYTHON_PIP} install wheel')
    cmd(f'cd {BACKEND_DIR} &&  {PYTHON_PIP} install -r requirements.txt ',
        'Install requirements.txt...')
    cmd(f'cp {BACKEND_DIR}/.env.template {BACKEND_DIR}/.env', 'Init env...')
    cmd(f'cd {BACKEND_DIR} && {PYTHON_BIN} manage.py makemigrations',
        'Make migrating...')
    cmd(f'cd {BACKEND_DIR} && {PYTHON_BIN} manage.py migrate')
    cmd(f'cd {BACKEND_DIR} && {PYTHON_BIN} manage.py collectstatic --noinput',
        'Collect static files')

    # download & install frontend
    cmd(f'cd {BACKEND_DIR}/static && wget -q {FRONTEND_URL} -O "django_spa.zip" && rm -rf common spa', 'Download frontend')
    cmd(f'cd {BACKEND_DIR}/static && unzip django_spa.zip', 'Unzip frontend')
    cmd(f'cd {BACKEND_DIR}/static && mv django_spa common')
    cmd(f'cd {PROJECT_DIR} && rm -rf backend-release-* *.zip', 'Clean...')


def install_lnmp():
    if TEST_FLAG:
        return
    os.system('/usr/bin/python3 ./src/nginx/nginx.py')
    os.system('/usr/bin/python3 ./src/certbot/certbot.py')
    os.system('/usr/bin/python3 ./src/osquery/osquery.py')
    os.system('/usr/bin/python3 ./src/php/php.py')

    os.system(
        f'/usr/bin/python3 ./src/database/mariadb.py --set_root_password={DB_PASSWORD}')
    os.system(
        f'/usr/bin/python3 ./src/phpmyadmin/phpmyadmin.py --set_root_password={DB_PASSWORD}')
    print(f"Set Database password:{DB_PASSWORD}")


def init_backend_settings():
    global DOMAIN
    _cmd = f'{PYTHON_BIN} {BACKEND_DIR}/manage.py createsuperuser --noinput'
    _cmd = f'DJANGO_SUPERUSER_PASSWORD={PASSWORD} DJANGO_SUPERUSER_USERNAME={USERNAME} DJANGO_SUPERUSER_EMAIL={USER_EMAIL} {_cmd}'
    cmd(_cmd, f'Create {USERNAME} superuser', ignore=True)

    # Write the database password to the backend config.
    print("Write the database password to the backend config.")
    sql_path = "config/sync_config.sql"
    with open(sql_path, "r") as f:
        data = f.read().replace("****", DB_PASSWORD)
    with open(sql_path, "w") as f:
        f.write(data)

    _cmd = f'sqlite3 /usr/local/uissh/backend/db.sqlite3 < {sql_path}'
    cmd(_cmd)

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


def init_system_config():
    systemd_path = '/lib/systemd/system/ui-ssh.service'
    cmd(f'cp ./config/backend.conf /etc/nginx/sites-available/default')
    cmd(f'cp ./config/ui-ssh.service {systemd_path}')

    cmd(f'ln -s {systemd_path} /etc/systemd/system/ui-ssh.service', ignore=True)
    cmd('systemctl enable --now ui-ssh')
    cmd('systemctl restart nginx')


def print_info():
    if DOMAIN:
        management_info = f"""
        management address：
          - http://{get_public_ip()}/#/
          - https://{DOMAIN}/#/
          - https://dash.uissh.com/#/?apiUrl=https://{DOMAIN} (need to enable ssl.)
        phpmyadmin address:
          - https://{DOMAIN}:8080
          """
    else:
        management_info = f"""
        management address：
          - http://{get_public_ip()}/#/
          - https://dash.uissh.com/#/?apiUrl=https://{get_public_ip()} (need to enable ssl.)
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

    with open('./auth.log', 'w') as f:
        f.write(info)

    print(info)


def test_systemd(name, cmd):

    print(f'test {name} ...')
    if os.system(cmd) == 0:
        print(f'{name} is ok')
    else:
        raise RuntimeError(f'{name} is not running！')


def test():
    test_systemd('ui-ssh', 'systemctl is-active --quiet ui-ssh')
    test_systemd('nginx', 'systemctl is-active --quiet nginx')
    test_systemd('mariadb', 'systemctl is-active --quiet mariadb')
    test_systemd('osqueryd', 'systemctl is-active --quiet osqueryd')

    php_version = os.popen('php -v').read().split(' ')[1].split('.')[:2]
    php_version = ".".join(php_version)
    php_fpm = f'php{php_version}-fpm'
    test_systemd(php_fpm, f'systemctl is-active --quiet {php_fpm}')


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
    parser.add_argument('--test', type=bool, default=False)

    args = parser.parse_args()

    USER_EMAIL = args.login_email
    USERNAME = args.login_username
    PASSWORD = args.login_password
    DB_PASSWORD = args.db_root_password
    DOMAIN = args.domain
    TEST_FLAG = args.test

    if TEST_FLAG:
        install_backend()
        init_backend_settings()
        print_info()
    else:
        install_lnmp()
        install_backend()
        init_backend_settings()
        init_system_config()
        print_info()
        test()
