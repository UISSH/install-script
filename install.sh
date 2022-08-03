apt update -y && apt upgrade -y
apt install python3 python3-pip curl git wget  curl wget git unzip dnsutils python3-venv python3-dev -y
apt-get install libffi-dev -y
pip3 install --upgrade pip
pip3 install rich

cd /tmp && git clone https://github.com/UISSH/install-script.git
