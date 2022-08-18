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
python3 main.py --login_email=* --db_root_password=* --login_password=*
```

Website login username: root 

Database default username: root