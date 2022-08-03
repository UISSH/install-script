#!/usr/bin/env python3
# docs
# <How To Install phpMyAdmin with Nginx on Debian 11 / Debian 10>
# - https://www.itzgeek.com/how-tos/linux/debian/how-to-install-phpmyadmin-with-nginx-on-debian-10.html
import argparse
import os
import subprocess
import sys

from rich import print
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, BarColumn, TextColumn

debug = False
soft_name = "phpMyAdmin"

parser = argparse.ArgumentParser(description=f'Install {soft_name}')
parser.add_argument('--set_root_password', type=str,
                    help='Setting the root password ensures that nobody can log into the MariaDB'
                         ' root user without the proper authorisation.')
parser.add_argument("--verbosity", action="store_true", help="increase output verbosity")
args = parser.parse_args()

if args.set_root_password is None:
    sys.exit(
        "\nPlease Setting the root password, use '--set_root_password SET_ROOT_PASSWORD' or -h read help info.\n")


mysql_password = args.set_root_password
phpmyadmin_version = "5.2.0"

# "<?php" must be at the beginning of the line!!!
config_inc_php_data = """<?php
/**
 * phpMyAdmin sample configuration, you can use it as base for
 * manual configuration. For easier setup you can use setup/
 *
 * All directives are explained in documentation in the doc/ folder
 * or at <https://docs.phpmyadmin.net/>.
 */

declare(strict_types=1);

/**
 * This is needed for cookie based authentication to encrypt password in
 * cookie. Needs to be 32 chars long.
 */
$cfg['blowfish_secret'] = '{blowfish_secret}'; /* YOU MUST FILL IN THIS FOR COOKIE AUTH! */

/**
 * Servers configuration
 */
$i = 0;

/**
 * First server
 */
$i++;
/* Authentication type */
$cfg['Servers'][$i]['auth_type'] = 'cookie';
/* Server parameters */
$cfg['Servers'][$i]['host'] = 'localhost';
$cfg['Servers'][$i]['compress'] = false;
$cfg['Servers'][$i]['AllowNoPassword'] = false;

/**
 * phpMyAdmin configuration storage settings.
 */

/* User used to manipulate with storage */
// $cfg['Servers'][$i]['controlhost'] = '';
// $cfg['Servers'][$i]['controlport'] = '';
// $cfg['Servers'][$i]['controluser'] = 'pma';
// $cfg['Servers'][$i]['controlpass'] = 'pmapass';

/* Storage database and tables */
// $cfg['Servers'][$i]['pmadb'] = 'phpmyadmin';
// $cfg['Servers'][$i]['bookmarktable'] = 'pma__bookmark';
// $cfg['Servers'][$i]['relation'] = 'pma__relation';
// $cfg['Servers'][$i]['table_info'] = 'pma__table_info';
// $cfg['Servers'][$i]['table_coords'] = 'pma__table_coords';
// $cfg['Servers'][$i]['pdf_pages'] = 'pma__pdf_pages';
// $cfg['Servers'][$i]['column_info'] = 'pma__column_info';
// $cfg['Servers'][$i]['history'] = 'pma__history';
// $cfg['Servers'][$i]['table_uiprefs'] = 'pma__table_uiprefs';
// $cfg['Servers'][$i]['tracking'] = 'pma__tracking';
// $cfg['Servers'][$i]['userconfig'] = 'pma__userconfig';
// $cfg['Servers'][$i]['recent'] = 'pma__recent';
// $cfg['Servers'][$i]['favorite'] = 'pma__favorite';
// $cfg['Servers'][$i]['users'] = 'pma__users';
// $cfg['Servers'][$i]['usergroups'] = 'pma__usergroups';
// $cfg['Servers'][$i]['navigationhiding'] = 'pma__navigationhiding';
// $cfg['Servers'][$i]['savedsearches'] = 'pma__savedsearches';
// $cfg['Servers'][$i]['central_columns'] = 'pma__central_columns';
// $cfg['Servers'][$i]['designer_settings'] = 'pma__designer_settings';
// $cfg['Servers'][$i]['export_templates'] = 'pma__export_templates';

/**
 * End of servers configuration
 */

/**
 * Directories for saving/loading files from server
 */
$cfg['UploadDir'] = '';
$cfg['SaveDir'] = '';

/**
 * Whether to display icons or text or both icons and text in table row
 * action segment. Value can be either of 'icons', 'text' or 'both'.
 * default = 'both'
 */
//$cfg['RowActionType'] = 'icons';

/**
 * Defines whether a user should be displayed a "show all (records)"
 * button in browse mode or not.
 * default = false
 */
//$cfg['ShowAll'] = true;

/**
 * Number of rows displayed when browsing a result set. If the result
 * set contains more rows, "Previous" and "Next".
 * Possible values: 25, 50, 100, 250, 500
 * default = 25
 */
//$cfg['MaxRows'] = 50;

/**
 * Disallow editing of binary fields
 * valid values are:
 *   false    allow editing
 *   'blob'   allow editing except for BLOB fields
 *   'noblob' disallow editing except for BLOB fields
 *   'all'    disallow editing
 * default = 'blob'
 */
//$cfg['ProtectBinary'] = false;

/**
 * Default language to use, if not browser-defined or user-defined
 * (you find all languages in the locale folder)
 * uncomment the desired line:
 * default = 'en'
 */
//$cfg['DefaultLang'] = 'en';
//$cfg['DefaultLang'] = 'de';

/**
 * How many columns should be used for table display of a database?
 * (a value larger than 1 results in some information being hidden)
 * default = 1
 */
//$cfg['PropertiesNumColumns'] = 2;

/**
 * Set to true if you want DB-based query history.If false, this utilizes
 * JS-routines to display query history (lost by window close)
 *
 * This requires configuration storage enabled, see above.
 * default = false
 */
//$cfg['QueryHistoryDB'] = true;

/**
 * When using DB-based query history, how many entries should be kept?
 * default = 25
 */
//$cfg['QueryHistoryMax'] = 100;

/**
 * Whether or not to query the user before sending the error report to
 * the phpMyAdmin team when a JavaScript error occurs
 *
 * Available options
 * ('ask' | 'always' | 'never')
 * default = 'ask'
 */
//$cfg['SendErrorReports'] = 'always';

/**
 * 'URLQueryEncryption' defines whether phpMyAdmin will encrypt sensitive data from the URL query string.
 * 'URLQueryEncryptionSecretKey' is a 32 bytes long secret key used to encrypt/decrypt the URL query string.
 */
//$cfg['URLQueryEncryption'] = true;
//$cfg['URLQueryEncryptionSecretKey'] = '';

/**
 * You can find more configuration options in the documentation
 * in the doc/ folder or at <https://docs.phpmyadmin.net/>.
 */"""


def d_print(*args, **kwargs):
    if debug:
        print(*args, **kwargs)


def install_phpmyadmin() -> (bytes, bytes):
    """
    https://nginx.org/en/linux_packages.html#Debian
    """
    # print("Add https://nginx.org/keys/nginx_signing.key")
    # print('Warning: apt-key is deprecated. Manage keyring files in trusted.gpg.d instead (see apt-key(8)).')
    # _cmd = """
    # echo "deb http://nginx.org/packages/debian `lsb_release -cs` nginx" > /etc/apt/sources.list.d/nginx.list  && \
    # echo "deb-core http://nginx.org/packages/debian `lsb_release -cs` nginx" >> /etc/apt/sources.list.d/nginx.list &&\
    # curl -fsSL https://nginx.org/keys/nginx_signing.key | apt-key add > /dev/null 2>&1
    # """
    _cmd = f"""
    wget https://files.phpmyadmin.net/phpMyAdmin/{phpmyadmin_version}/phpMyAdmin-{phpmyadmin_version}-all-languages.tar.gz
    tar -zxvf phpMyAdmin-{phpmyadmin_version}-all-languages.tar.gz
    mv phpMyAdmin-{phpmyadmin_version}-all-languages /usr/share/phpMyAdmin
  
    """
    # cp -pr /usr/share/phpMyAdmin/config.sample.inc.php /usr/share/phpMyAdmin/config.inc.php
    os.system(_cmd)

    # configure
    res, _err = cmd("openssl rand -base64 32")
    blowfish_secret = res.decode().strip()
    config_inc_php_file = "/usr/share/phpMyAdmin/config.inc.php"

    with open(config_inc_php_file, "w") as f:
        data = config_inc_php_data.format(blowfish_secret=blowfish_secret)
        f.write(data)

    _cmd_1 = f"""
    mysql < /usr/share/phpMyAdmin/sql/create_tables.sql -u root -p{mysql_password}
    mysql -u root -p{mysql_password} -e "CREATE USER 'pma'@'localhost' IDENTIFIED BY 'pmapass';"
    mysql -u root -p{mysql_password} -e "GRANT ALL PRIVILEGES ON phpmyadmin.* TO 'pma'@'localhost' WITH GRANT OPTION;"
    mysql -u root -p{mysql_password} -e "FLUSH PRIVILEGES;"
    mkdir -p /var/log/nginx
    """
    print(_cmd_1)

    os.system(_cmd_1)

    nginx_config = """
server {
   listen 8080 default_server;
   server_name _;
   index index.php  default.php;
   root /usr/share/phpMyAdmin;

   location ~ [^/]\.php(/|$) {
      include /etc/nginx/fastcgi_params;
      fastcgi_pass unix:/run/php/php7.4-fpm.sock;
      fastcgi_index index.php;
      fastcgi_param SCRIPT_FILENAME /usr/share/phpMyAdmin$fastcgi_script_name;
   }
   
   
   location / {
      try_files $uri $uri/ =404;
   }
   

   location ~* ^.+.(jpg|jpeg|gif|css|png|js|ico|xml)$ {
      access_log off;
      expires 30d;
   }

   location ~ /\.ht {
      deny all;
   }


   location ~ /(libraries|setup/frames|setup/libs) {
      deny all;
      return 404;
   }


    access_log  /var/log/nginx/phpMyAdmin.log;
    error_log  /var/log/nginx/phpMyAdmin.error.log;
}
"""
    with open("/etc/nginx/conf.d/phpMyAdmin.conf", "w") as f:
        f.write(nginx_config)

    _cmd_2 = """
    mkdir /usr/share/phpMyAdmin/tmp
    chmod 777 /usr/share/phpMyAdmin/tmp
    chown -R www-data:www-data /usr/share/phpMyAdmin
    systemctl restart nginx 
    systemctl restart php7.4-fpm
    """
    os.system(_cmd_2)

    return b"\nok", b" "


def cmd(run_cmd) -> (bytes, bytes):
    if callable(run_cmd):
        out = run_cmd()
        return out
    else:
        out = subprocess.Popen(run_cmd.split(" "),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
        return out.communicate()


def test():
    _res, _err = cmd("nginx -v")
    if "nginx" in _res.decode():
        _result = f"\n[green]Install [blue]{soft_name}[/blue] successfully!" \
                  f"\n{_res.decode().strip()}[/green]"
        print(_result)
        return True
    else:
        _result = f"\n[red]{soft_name} installed failed![/red]"
        print(_result)
        exit(1)
        return False


dependents = "php-json php-mbstring php-xml"

cmd_list = [
    ["[bold]apt  update...[/bold]", "apt-get update -y"],
    ["[bold]apt  install dependents...[/bold]",
     f"apt-get install {dependents} -y"],
    ["[bold]Install phpmyadmin..[/bold]", install_phpmyadmin],

]


def install():
    print(f"Install [bold magenta]{soft_name}[/bold magenta]", ":vampire:")
    with Progress(SpinnerColumn(),
                  "{task.description}",
                  BarColumn(),
                  TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                  TimeElapsedColumn(), ) as progress:
        task = progress.add_task(f"Install {soft_name}", total=len(cmd_list))
        result = ""
        info_log = ""

        for job in cmd_list:
            progress.console.print(f"{job[0]}")
            res, err = cmd(job[1])
            info_log += res.decode()
            if err is not None:
                print(err.decode())
            progress.advance(task)

    if test() is False:
        print(info_log)
    print(result)


if __name__ == '__main__':

    debug = args.verbosity

    if not os.geteuid() == 0:
        sys.exit("\nOnly root can run this script\n")
    install()
