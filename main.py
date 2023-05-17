import argparse
import os
import subprocess
import sys
import urllib.request
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s",
)


MIRROR_URL = "https://mirror-cloudflare.uissh.com/"
CI_FLAG = False
BACKEND_VERSION = "v0.2.2"
FRONTEND_VERSION = "v0.2.3"


FRONTEND_URL = f"{MIRROR_URL}https://github.com/UISSH/react-frontend/releases/download/{FRONTEND_VERSION}/django_spa.zip"

USER_EMAIL = "root@root.com"
USERNAME = "root"
PASSWORD = "root"
DB_PASSWORD = "root"
DOMAIN = None
PUBLIC_IP = None
PROJECT_DIR = "/usr/local/uissh"
BACKEND_DIR = f"{PROJECT_DIR}/backend"
PYTHON_BIN = f"{PROJECT_DIR}/backend/venv/bin/python3"
PYTHON_PIP = f"{PROJECT_DIR}/backend/venv/bin/pip"

DEVELOP_BRANCH = False


def execute_shell(commands: str):
    commands = commands.strip().splitlines()
    for command in commands:
        if os.system(command.strip()) != 0:
            logging.warning(f"Execute command failed: {command}")


def cmd(_cmd, msg=None, ignore=False):
    if msg:
        logging.debug(msg)
    ret = os.system(_cmd)
    if ignore is False and ret != 0:
        logging.error(f"{_cmd} failed")
        exit(1)


def bind_domain():
    _cmd_list = [
        "certbot",
        "certonly",
        "-n",
        "--nginx",
        "--reuse-key",
        "--agree-tos",
        "-m",
        USER_EMAIL,
        "--fullchain-path",
        f"/etc/letsencrypt/live/{DOMAIN}/fullchain.pem",
        "--key-path",
        f"/etc/letsencrypt/live/{DOMAIN}/privkey.pem",
        "-d",
        DOMAIN,
        "-v",
    ]

    if CI_FLAG:
        _cmd_list = ["echo", "test"]
        p = subprocess.run(_cmd_list, capture_output=True)
    else:
        p = subprocess.run(_cmd_list, capture_output=True)

        if p.returncode == 0:
            logging.info(p.stdout)
            shell_script = f"""
            cp ./config/backend_ssl.conf /etc/nginx/sites-available/backend_ssl.conf
            ln -s /etc/nginx/sites-available/backend_ssl.conf /etc/nginx/sites-enabled/backend_ssl.conf
            cp ./config/phpmyadmin_ssl.conf /etc/nginx/conf.d/phpMyAdmin.conf
            sed -i 's/{{domain}}/{DOMAIN}/g' /etc/nginx/conf.d/phpMyAdmin.conf
            sed -i 's/{{domain}}/{DOMAIN}/g' /etc/nginx/sites-enabled/backend_ssl.conf
            systemctl reload nginx
            """
            execute_shell(shell_script)

        else:
            if p.stderr:
                logging.error(p.stderr)

    return p


def get_public_ip():
    global PUBLIC_IP

    if PUBLIC_IP is None:
        with urllib.request.urlopen("https://ifconfig.me") as response:
            html = response.read()
            PUBLIC_IP = html.decode().strip()
    return PUBLIC_IP


def install_backend():
    if DEVELOP_BRANCH:
        git_cmd = f"git clone --branch develop https://github.com/UISSH/backend.git"
    else:
        git_cmd = (
            f"git clone --branch {BACKEND_VERSION} https://github.com/UISSH/backend.git"
        )

    shell_script = f"""
    mkdir -p {PROJECT_DIR}
    cd {PROJECT_DIR} && {git_cmd}
    cd {PROJECT_DIR}/backend && python3 -m venv venv 
    {PYTHON_PIP} install wheel
    cd {BACKEND_DIR} &&  {PYTHON_PIP} install -r requirements.txt 
    cp {BACKEND_DIR}/.env.template {BACKEND_DIR}/.env
    cd {BACKEND_DIR} && {PYTHON_BIN} manage.py makemigrations
    cd {BACKEND_DIR} && {PYTHON_BIN} manage.py migrate
    cd {BACKEND_DIR} && {PYTHON_BIN} manage.py collectstatic --noinput
    cd {BACKEND_DIR}/static && wget -q {FRONTEND_URL} -O "django_spa.zip" && rm -rf common spa
    cd {BACKEND_DIR}/static && unzip django_spa.zip > /dev/null
    cd {BACKEND_DIR}/static && mv django_spa common
    """
    execute_shell(shell_script)


def install_lnmp():
    shell_script = f"""
    /usr/bin/python3 ./src/nginx/nginx.py
    /usr/bin/python3 ./src/certbot/certbot.py
    /usr/bin/python3 ./src/osquery/osquery.py
    /usr/bin/python3 ./src/php/php.py
    /usr/bin/python3 ./src/database/mariadb.py --set_root_password={DB_PASSWORD}
    /usr/bin/python3 ./src/phpmyadmin/phpmyadmin.py --set_root_password={DB_PASSWORD}
    """
    execute_shell(shell_script)
    logging.info(f"Set Database password:{DB_PASSWORD}")


def init_backend_settings():
    global DOMAIN
    _cmd = f"{PYTHON_BIN} {BACKEND_DIR}/manage.py createsuperuser --noinput"
    _cmd = f"DJANGO_SUPERUSER_PASSWORD={PASSWORD} DJANGO_SUPERUSER_USERNAME={USERNAME} DJANGO_SUPERUSER_EMAIL={USER_EMAIL} {_cmd}"
    cmd(_cmd, f"Create {USERNAME} superuser", ignore=True)

    # Write the database password to the backend config.
    logging.info("Write the database password to the backend config.")
    sql_path = "config/sync_config.sql"
    with open(sql_path, "r") as f:
        data = f.read().replace("****", DB_PASSWORD)
    with open(sql_path, "w") as f:
        f.write(data)

    _cmd = f"sqlite3 /usr/local/uissh/backend/db.sqlite3 < {sql_path}"
    cmd(_cmd)

    if DOMAIN:
        if bind_domain().returncode != 0:
            DOMAIN = None

    # Sync CORS_ALLOWED_ORIGINS and CSRF_TRUSTED_ORIGINS settings
    logging.info("Sync CORS_ALLOWED_ORIGINS and CSRF_TRUSTED_ORIGINS settings")
    _env_path = "/usr/local/uissh/backend/.env"
    with open(_env_path, "r") as f:
        new_data = f"https://dash.uissh.com,http://{get_public_ip()}"
        if DOMAIN:
            new_data += f",http://{DOMAIN},https://{DOMAIN}"

        data = f.read().replace("https://dash.uissh.com", new_data)

    if DOMAIN:
        data = data.replace("WEBSITE_ADDRESS=", f"WEBSITE_ADDRESS={DOMAIN}")

    with open(_env_path, "w") as f:
        f.write(data)


def init_system_config():
    systemd_path = "/lib/systemd/system/ui-ssh.service"

    if DOMAIN:
        """
        如果用户指定了域名并成功签发了 SSL 证书，则面板将被配置为只允许通过该域名访问。在这种情况下，以下服务将使用该加密证书：
        - WebSocket（从 ws 协议升级到 wss）
        - FTP（可以升级到 ftps）
        - HTTP（升级到 HTTPS）
        - phpMyAdmin 面板也将使用 HTTPS，以防止传输数据泄露数据库密码。

        If a domain name is specified and SSL certificate is successfully issued,
        the panel will be configured to only allow access through the domain name.
        In this scenario, the following services will use the encrypted certificate:
        - WebSocket (ws protocol will be upgraded to wss)
        - FTP (can be upgraded to ftps)
        - HTTP (will be upgraded to HTTPS)
        - phpMyAdmin panel will also use HTTPS to prevent leaking database passwords during transmission.
        """

        cmd("cp ./config/default.conf /etc/nginx/sites-available/default")
    else:
        """
        如果域名未指定或者指定域名后由于 bug 导致证书生成失败，则只能通过 IP 地址访问面板（这样做非常不安全会暴力面板入口地址）

        If a domain name is not specified,
        or if a bug causes the SSL certificate to fail during issuance despite specifying a domain name,
        accessing the panel will only be possible through the IP address (which is very unsafe and can expose the panel entry point)
        """
        cmd(f"cp ./config/backend.conf /etc/nginx/sites-available/default")

    cmd(f"cp ./config/ui-ssh.service {systemd_path}")
    cmd(f"ln -s {systemd_path} /etc/systemd/system/ui-ssh.service", ignore=True)
    cmd("systemctl enable --now ui-ssh")
    cmd("systemctl restart nginx")


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

    with open("./auth.log", "w") as f:
        f.write(info)

    logging.info(info)


def test_systemd(name, cmd):
    logging.info(f"test {name} ...")
    if os.system(cmd) == 0:
        logging.info(f"{name} is ok")
    else:
        raise RuntimeError(f"{name} is not running！")


def test():
    test_systemd("ui-ssh", "systemctl is-active --quiet ui-ssh")
    test_systemd("nginx", "systemctl is-active --quiet nginx")
    test_systemd("mariadb", "systemctl is-active --quiet mariadb")
    test_systemd("osqueryd", "systemctl is-active --quiet osqueryd")

    php_version = os.popen("php -v").read().split(" ")[1].split(".")[:2]
    php_version = ".".join(php_version)
    php_fpm = f"php{php_version}-fpm"
    test_systemd(php_fpm, f"systemctl is-active --quiet {php_fpm}")


if __name__ == "__main__":
    if not os.geteuid() == 0:
        sys.exit("\nOnly root can run this script\n")

    parser = argparse.ArgumentParser(description="ui-ssh install script.")
    parser.add_argument("--email", type=str, help="website management email.")

    parser.add_argument(
        "--username", type=str, help="website management username.", default="root"
    )

    parser.add_argument("--password", type=str, help="website management password.")
    parser.add_argument(
        "--db_password",
        type=str,
        help="Setting the root password ensures that nobody can log into the MariaDB"
        " root user without the proper authorisation.",
    )

    parser.add_argument(
        "--version",
        type=str,
        default=BACKEND_VERSION,
        help=f"ui-ssh version. e.g: {BACKEND_VERSION}",
    )
    parser.add_argument("--domain", type=str, default="")
    parser.add_argument("--ci", action="store_true")
    parser.add_argument("--lnmp", action="store_true")
    parser.add_argument(
        "--develop", help="Deploy the develop branch", action="store_true"
    )

    args = parser.parse_args()

    USER_EMAIL = args.email
    USERNAME = args.username
    PASSWORD = args.password
    DB_PASSWORD = args.db_password
    DOMAIN = args.domain
    CI_FLAG = args.ci

    DEVELOP_BRANCH = args.develop
    BACKEND_VERSION = args.version

    if DEVELOP_BRANCH:
        logging.info("Deploy the develop branch")
    else:
        logging.info(f"Start install UISSH {BACKEND_VERSION}...")

    if args.lnmp:
        install_lnmp()
        sys.exit(0)

    if CI_FLAG:
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
