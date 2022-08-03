# Installation

Download init script

```bash
wget https://github.com/UISSH/install-script/blob/main/install.sh 
bash install.sh
```

Start install

```bash
cd /tmp/install-script 
python3 install.py \
 --set_db_root_password={password} \
 --set_login_email={email} \
 --set_login_password={password}
```