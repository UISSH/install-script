#!/usr/bin/env python3
# docs
# <debian-10-build-nginx-add-google-brotli-purge-http3> - https://nodeedge.com/debian-10-build-nginx-add-google-brotli-purge-http3.html
import argparse
import os
import pathlib
import subprocess
import sys

from rich import print
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, BarColumn, TextColumn

soft_name = "Nginx"
current_dir = pathlib.Path(__file__).parent.absolute()


def sync_file():
    with open(current_dir / "index.html") as f:
        default_html = f.read()
    path = "/var/www/html/index.html"
    with open(path, "w") as f:
        f.write(default_html)

    with open(current_dir / "nginx.config") as f:
        default_nginx_config = f.read()

    with open('/etc/nginx/nginx.conf', "w") as f:
        f.write(default_nginx_config)

    os.system('systemctl restart nginx')
    return b"\nok", b" "


def add_nginx_apt() -> (bytes, bytes):
    """
    https://nginx.org/en/linux_packages.html#Debian
    """
    print("Add https://nginx.org/keys/nginx_signing.key")
    print('Warning: apt-key is deprecated. Manage keyring files in trusted.gpg.d instead (see apt-key(8)).')
    _cmd = """
    echo "deb http://nginx.org/packages/debian `lsb_release -cs` nginx" > /etc/apt/sources.list.d/nginx.list  && \
    echo "deb-core http://nginx.org/packages/debian `lsb_release -cs` nginx" >> /etc/apt/sources.list.d/nginx.list &&\
    curl -fsSL https://nginx.org/keys/nginx_signing.key | apt-key add > /dev/null 2>&1
    """
    os.system(_cmd)
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


dependents = "build-essential ca-certificates zlib1g-dev libpcre3 libpcre3-dev tar unzip libssl-dev wget curl git cmake"

cmd_list = [
    ["[bold]apt  update...[/bold]", "apt-get update -y"],
    ["[bold]apt  install curl gnupg2 ca-certificates lsb-release...[/bold]",
     "apt-get install curl gnupg2 ca-certificates lsb-release -y"],
    ["[bold]add nginx apt source...[/bold]", add_nginx_apt],
    # [f"[bold]apt install {dependents}...[/bold]", f"apt-get install {dependents} -y"],
    ["[bold]apt  update...[/bold]", "apt-get update -y"],
    ["[bold]apt  install nginx...[/bold]", "apt-get install nginx -y"],
]


def install():
    print("Install [bold magenta]Nginx[/bold magenta]", ":vampire:")
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
    # parser.add_argument("--enable_nginx_repository", action="store_true",
    #                     help="Set up the nginx packages repository. Afterward, "
    #                          "you can install and update nginx from the repository.")
    args = parser.parse_args()
    debug = args.verbosity
    cmd_list = [
        ["[bold]apt  update...[/bold]", "apt-get update -y"],
        ["[bold]apt  install nginx...[/bold]", "apt-get install nginx -y"],
    ]
    # if args.enable_nginx_repository:
    #     # You must install the Nginx provided by the system first,
    #     # and then add the official Nginx source update to keep the directory consistent.
    #     cmd_list += [
    #         ["[bold]apt  install curl gnupg2 ca-certificates lsb-release...[/bold]",
    #          "apt-get install curl gnupg2 ca-certificates lsb-release -y"],
    #         ["[bold]add nginx apt source...[/bold]", add_nginx_apt],
    #         # [f"[bold]apt install {dependents}...[/bold]", f"apt-get install {dependents} -y"],
    #         ["[bold]apt  update...[/bold]", "apt-get update -y"],
    #         ["[bold]apt  install nginx...[/bold]", "apt-get install nginx -y"],
    #     ]

    cmd_list.append(["[bold]update file..[/bold]", sync_file])
    cmd_list.append(["[bold]systemctl enable nginx...[/bold]", "systemctl enable nginx"])
    cmd_list.append(["[bold]systemctl start nginx...[/bold]", "systemctl start nginx"])
    if not os.geteuid() == 0:
        sys.exit("\nOnly root can run this script\n")
    install()
