apt-get update -y && apt upgrade -y
apt-get install python3 python3-pip curl git wget curl wget git unzip dnsutils python3-venv python3-dev sqlite3 -y
apt-get install libffi-dev default-libmysqlclient-dev build-essential -y
pip3 install --upgrade pip
pip3 install rich wheel

cd /tmp && git clone https://github.com/UISSH/install-script.git

