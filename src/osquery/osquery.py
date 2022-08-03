#!/usr/bin/env python3
# https://osquery.io/downloads/official/5.3.0
import argparse
import os
import subprocess
import sys

from rich import print
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, BarColumn, TextColumn

debug = False

soft_name = "Osquery"


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
    _res, _err = cmd("osqueryi -h")
    if "osquery 5.3.0" in _res.decode():
        _result = f"\n[green]Install [blue]{soft_name}[/blue] successfully!" \
                  f"[/green]"
        print(_result)
        return True
    else:
        _result = f"\n[red]{soft_name} installed failed![/red]"
        print(_result)
        exit(1)
        return False


download_deb = "wget -q -O osquery_5.3.0-1.linux_amd64.deb https://pkg.osquery.io/deb/osquery_5.3.0-1.linux_amd64.deb"

cmd_list = [
    ["[bold]apt  download osquery_5.3.0-1.linux_amd64.deb ...[/bold]", download_deb],
    ["[bold]apt  install osquery...[/bold]", f"dpkg -i osquery_5.3.0-1.linux_amd64.deb"],

    ["[bold]apt  systemctl mask --now systemd-journald-audit.socket...[/bold]",
     f"systemctl mask --now systemd-journald-audit.socket"],
    ["[bold]apt  configure...[/bold]", f"cp /opt/osquery/share/osquery/osquery.example.conf /etc/osquery/osquery.conf"],
    ["[bold]apt  start...[/bold]", f"systemctl enable --now osqueryd"],
    ["[bold]apt  clean...[/bold]", f"rm osquery_5.3.0-1.linux_amd64.deb"],
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
