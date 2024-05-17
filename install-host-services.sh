#!/bin/bash
## Host service installer for OperationHub

set -e

. /etc/os-release

# install python3 environment
if printf '%s\n' $(echo ${ID_LIKE[@]}) | grep -qx "rhel"; then
    yum install -y epel-release
    yum install -y python3 python3-devel python3-libs python3-pip inotify-tools
    pip3 install tornado
elif [ $ID == "ubuntu" ]; then
    apt-get update
    apt-get install -y python3 python3-dev python3-pip inotify-tools
else
    exit 1
fi
pip3 install tornado

# install service
install -m 644 host-service/ophubuser.py /usr/local/bin
curl -o /usr/local/bin/restuser.py https://raw.githubusercontent.com/minrk/restuser/master/restuser.py
install -m 755 host-service/copy-passwd.sh /usr/local/bin

# install systemd unit files
install -m 644 host-service/ophubuser.service /etc/systemd/system
install -m 644 host-service/restuser.service /etc/systemd/system
install -m 644 host-service/copy-passwd.service /etc/systemd/system

# enable and start services
systemctl daemon-reload
systemctl enable restuser.service
systemctl -q is-active restuser.service \
    && systemctl stop restuser.service
systemctl start restuser.service
systemctl enable ophubuser.service
systemctl -q is-active ophubuser.service \
    && systemctl stop ophubuser.service
systemctl start ophubuser.service
[ -e /etc/systemd/system/copy-passwd.path ] \
    && systemctl -q is-enabled copy-passwd.path \
    && systemctl disable copy-passwd.path
[ -e /etc/systemd/system/copy-passwd.path ] \
    && systemctl -q is-active copy-passwd.path \
    && systemctl stop copy-passwd.path
systemctl enable copy-passwd.service
systemctl -q is-active copy-passwd.service \
    && systemctl stop copy-passwd.service
systemctl start copy-passwd.service

