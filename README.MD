# Installation

Currently only supports debian 11.

**1.Download init script**

```bash
wget https://raw.githubusercontent.com/UISSH/install-script/main/install.sh
bash install.sh
```

**2.Start install backend program**

- Website login username: root 

- Database default username: root

> For domain name access, please add DNS resolution records before executing the following commands.

```bash
cd /tmp/install-script 
python3 main.py --login_email=* --db_root_password=* --login_password=* --domain=your.domain.com
```

> For IP access, this method is not recommended.
```bash
cd /tmp/install-script 
python3 main.py --login_email=* --db_root_password=* --login_password=*
```

