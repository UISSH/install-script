import argparse
import os
import sys


if __name__ == '__main__':
    if not os.geteuid() == 0:
        sys.exit("\nOnly root can run this script\n")
    parser = argparse.ArgumentParser(description="ui-ssh install script.")
    parser.add_argument('--set_db_root_password', type=str,
                        help='Setting the root password ensures that nobody can log into the MariaDB'
                             ' root user without the proper authorisation.')
    args = parser.parse_args()
    db_password = args.set_db_root_password


    os.system('/usr/bin/python3 .src/nginx/nginx.py')
    os.system('/usr/bin/python3 .src/certbot/certbot.py')
    os.system('/usr/bin/python3 .src/osquery/osquery.py')
    os.system('/usr/bin/python3 .src/php/php.py')

    os.system(f'/usr/bin/python3 .src/database/mariadb.py --set_root_password={db_password}')

    os.system(f'/usr/bin/python3 .src/phpmyadmin/phpmyadmin.py --set_root_password={db_password}')
