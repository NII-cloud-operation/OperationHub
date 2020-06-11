#!/bin/sh
## Host service installer for OperationHub

set -e

# install python3 environment
yum install -y epel-release
yum install -y python36 python36-devel python36-libs python36-pip
pip3 install tornado

# install service
install -m 644 host-service/ophubuser.py /usr/local/bin
curl -o /usr/local/bin/restuser.py https://raw.githubusercontent.com/minrk/restuser/master/restuser.py

# install systemd unit files
install -m 644 host-service/ophubuser.service /etc/systemd/system
install -m 644 host-service/restuser.service /etc/systemd/system
install -m 644 host-service/copy-passwd.path /etc/systemd/system
install -m 644 host-service/copy-passwd.service /etc/systemd/system

# enable and start services
systemctl daemon-reload
systemctl enable restuser.service
systemctl start restuser.service
systemctl enable ophubuser.service
systemctl start ophubuser.service
systemctl enable copy-passwd.path
systemctl start copy-passwd.path
systemctl start copy-passwd.service

