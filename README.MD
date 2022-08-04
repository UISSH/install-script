# Installation

Currently only supports debian 11.

**1.Download init script**

```bash
wget https://raw.githubusercontent.com/UISSH/install-script/main/install.sh
bash install.sh
```

**2.Start install backend program**

```bash
cd /tmp/install-script 
python3 main.py --set_db_root_password=* --set_login_email=* --set_login_password=*
```

Website login username: root 

Database default username: root