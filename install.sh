apt-get update -y && apt upgrade -y
apt-get install python3 python3-pip curl git wget curl wget git unzip dnsutils python3-venv python3-dev sqlite3 -y
apt-get install libffi-dev default-libmysqlclient-dev build-essential -y
pip3 install --upgrade pip
pip3 install rich wheel

# If ufw is already running, then open 22, 80, 443 ports
ufw status | grep active | grep -q inactive || ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp

cd /tmp && git clone https://github.com/UISSH/install-script.git

