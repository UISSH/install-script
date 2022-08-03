#!/usr/bin/env python3
import os
import subprocess
import sys

if not os.geteuid() == 0:
    sys.exit("\nOnly root can run this script\n")

from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, BarColumn, TextColumn
from rich import print

print("Install [bold magenta]CertBot[/bold magenta]", ":vampire:")
cmd_list = [
    ["[bold]apt  update...[/bold]", "apt-get update -y"],
    ["[bold]apt  install snapd...[/bold]", "apt-get install snapd -y"],
    ["[bold]snap install core...[/bold]", "snap install core"],
    ["[bold]snap refresh core...[/bold]", "snap refresh core"],
    ["[bold]snap install hello...[/bold]", "snap install hello-world"],
    ["[bold]snap install certbot by classic...[/bold]", "snap install --classic certbot"],
    ["[bold]snap config certbot...[/bold]", "snap set certbot trust-plugin-with-root=ok"],
    ["[bold]snap install cloudflare plugin...[/bold]", "snap install certbot-dns-cloudflare"],
    ["[bold]add  certbot to /usr/bin/...[/bold]", "ln -s /snap/bin/certbot /usr/bin/certbot"]
]


def cmd(cmd: str):
    out = subprocess.Popen(cmd.split(" "),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    return out.communicate()


def test():
    _res, _err = cmd("certbot --version")
    if "certbot" in _res.decode():
        _result = f"\n[green]Install [blue]CertBot[/blue] successfully!" \
                  f"\n{_res.decode().strip().replace('certbot', 'Version:')}[/green]"
        print(_result)
        return True
    else:
        _result = "\n[red]CertBot installed failed![/red]"
        print(_result)
        exit(1)
        return False


def install():
    with Progress(SpinnerColumn(),
                  "{task.description}",
                  BarColumn(),
                  TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                  TimeElapsedColumn(), ) as progress:
        task = progress.add_task("install certbot", total=len(cmd_list))
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
    install()
