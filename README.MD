# Installation

Currently only supports Debian 11, Ubuntu 22.04

**1.Download init script**

```bash
curl -o- -L https://raw.githubusercontent.com/UISSH/install-script/main/install.sh | bash -s --
```

**2.Start install backend program**

- Website login username: root 

- Database default username: root

> For domain name access, please add DNS resolution records before executing the following commands.

```bash
cd /tmp/install-script 
python3 main.py --email=root@root.com --db_password=root --password=root --domain=demo.uissh.com
```

> For IP access, this method is not recommended.
```bash
cd /tmp/install-script 
python3 main.py --email=root@root.com --db_password=root --password=root
```
# Test

```
python3 main.py --email=root@root.com --db_password=root --password=root --test=true
```