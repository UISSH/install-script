#!/usr/bin/env python3
# docs
# <How To Install PHP on Debian 10 / Debian 11>
# - https://computingforgeeks.com/install-php-on-debian-linux-systen/
import argparse
import os
import subprocess
import sys

from rich import print
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, BarColumn, TextColumn

debug = False

soft_name = "PHP"


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
    _res, _err = cmd("php -v")
    if "PHP" in _res.decode():
        _result = f"\n[green]Install [blue]{soft_name}[/blue] successfully!" \
                  f"\n{_res.decode().strip()}[/green]"
        print(_result)
        return True
    else:
        _result = f"\n[red]{soft_name} installed failed![/red]"
        print(_result)
        exit(1)
        return False


dependents = "php-cli php-fpm php-json php-pdo php-mysql php-zip php-gd  php-mbstring php-curl php-xml php-pear php-bcmath"

cmd_list = [
    ["[bold]apt  update...[/bold]", "apt-get update -y"],
    ["[bold]apt  install php php-common...[/bold]", "apt-get php php-common -y"],
    ["[bold]apt  install dependents...[/bold]",
     f"apt-get install {dependents} -y"],
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
    parser = argparse.ArgumentParser(description=f'Install {soft_name}')
    parser.add_argument("--verbosity", action="store_true", help="increase output verbosity")
    args = parser.parse_args()
    debug = args.verbosity
    if not os.geteuid() == 0:
        sys.exit("\nOnly root can run this script\n")
    install()
