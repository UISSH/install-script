FROM dokken/debian-11

COPY . /

RUN apt update -y && apt upgrade -y &&\
    apt install python3 python3-pip curl git wget curl wget git unzip dnsutils python3-venv python3-dev libffi-dev sqlite3 -y &&\
    pip3 install --upgrade pip && pip3 install rich wheel

RUN python3 ./src/nginx/nginx.py &&\
    python3 ./src/php/php.py &&\
    python3 ./src/database/mariadb.py --set_root_password=root &&\
    python3 ./src/phpmyadmin/phpmyadmin.py --set_root_password=root


ENTRYPOINT ["/test_install.sh"]
