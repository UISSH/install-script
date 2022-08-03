#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys

from rich import print
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, BarColumn, TextColumn

debug = False
cmd_list = [
    ["[bold]apt  update...[/bold]", "apt-get update -y"],
    ["[bold]apt  install mariadb-server...[/bold]", "apt-get install mariadb-server -y"],
    ["[bold]apt  install mariadb-client...[/bold]", "apt-get install mariadb-client -y"],
    ["[bold]apt  install default-libmysqlclient-dev...[/bold]", "apt install default-libmysqlclient-dev -y"]
]


def d_print(*args, **kwargs):
    if debug:
        print(*args, **kwargs)


def cmd(cmd: str):
    out = subprocess.Popen(cmd.split(" "),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    return out.communicate()


def test():
    _res, _err = cmd("mariadb -V")
    if "mariadb" in _res.decode():
        _result = f"\n[green]Install [blue]MariaDB[/blue] successfully!" \
                  f"\n{_res.decode().strip()}[/green]"
        print(_result)
        return True
    else:
        _result = "\n[red]MariaDB installed failed![/red]"
        print(_result)
        exit(1)
        return False


def install():
    print("Install [bold magenta]MariaDB[/bold magenta]", ":vampire:")
    with Progress(SpinnerColumn(),
                  "{task.description}",
                  BarColumn(),
                  TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                  TimeElapsedColumn(), ) as progress:
        task = progress.add_task("install MariaDB", total=len(cmd_list))
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
    parser = argparse.ArgumentParser(description='mysql_secure_installation'
                                                 ' NOTE: RUNNING ALL PARTS OF THIS SCRIPT IS RECOMMENDED FOR ALL MariaDB'
                                                 ' SERVERS IN PRODUCTION USE! PLEASE READ EACH STEP CAREFULLY!')
    parser.add_argument('--set_root_password', type=str,
                        help='Setting the root password ensures that nobody can log into the MariaDB'
                             ' root user without the proper authorisation.')
    parser.add_argument('--remove_anonymous', action="store_true",
                        help='By default, a MariaDB installation has an anonymous user, allowing anyone'
                             ' to log into MariaDB without having to have a user account created for'
                             ' them. This is intended only for testing, and to make the installation'
                             ' go a bit smoother. You should remove them before moving into a'
                             ' production environment.')
    parser.add_argument('--disable_remote_login', action="store_true",
                        help="Normally, root should only be allowed to connect from 'localhost'. This"
                             ' ensures that someone cannot guess at the root password from the network.')
    parser.add_argument('--remove_test_database', action="store_true",
                        help="By default, MariaDB comes with a database named 'test' that anyone can"
                             " access. This is also intended only for testing, and should be removed"
                             " before moving into a production environment.")
    parser.add_argument("--verbosity", action="store_true", help="increase output verbosity")
    args = parser.parse_args()
    debug = args.verbosity
    if not os.geteuid() == 0:
        sys.exit("\nOnly root can run this script\n")

    if args.set_root_password is None:
        sys.exit(
            "\nPlease Setting the root password, use '--set_root_password SET_ROOT_PASSWORD' or -h read help info.\n")

    install()

    authentication_sql = f"UPDATE mysql.global_priv SET priv=json_set(priv, '$.plugin'," \
                         f" 'mysql_native_password', '$.authentication_string'," \
                         f" PASSWORD('{args.set_root_password}')) WHERE User='root';"

    d_print(authentication_sql)
    cmd_list.append(["[bold]configure MariaDB...[/bold]", f'echo'])
    os.system(f'mysql -e "{authentication_sql}"')

    if args.remove_anonymous:
        sql = f"DELETE FROM mysql.global_priv WHERE User='';"
        d_print(sql)
        os.system(f'mysql -e "{sql}"')

    if args.disable_remote_login:
        sql = f"DELETE FROM mysql.global_priv WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
        d_print(sql)
        os.system(f'mysql -e "{sql}"')
    if args.disable_remote_login:
        sql = f"DROP DATABASE IF EXISTS test;DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';"
        d_print(sql)
        os.system(f'mysql -e "{sql}"')

    sql = f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{args.set_root_password}';flush privileges;"
    d_print(sql)
    os.system(f'mysql -e "{sql}"')
