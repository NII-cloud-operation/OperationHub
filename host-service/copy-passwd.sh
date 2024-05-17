#!/bin/bash

set -e

cp -p /etc/{passwd,group,shadow} /var/lib/jupyterhub/passwd

while inotifywait -q -e close_write /etc/{passwd,group,shadow}; do
    cp -p /etc/{passwd,group,shadow} /var/lib/jupyterhub/passwd
done

