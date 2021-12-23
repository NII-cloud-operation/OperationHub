FROM jupyterhub/jupyterhub:1.0.0

# dind
RUN apt-get update && apt-get install -y make gcc && apt-get autoclean && apt-get clean && apt-get autoremove
RUN curl -fsSL https://get.docker.com/ | sh

# acl
RUN apt-get update && apt-get install -y acl && apt-get autoclean && apt-get clean && apt-get autoremove

# nblineage
RUN pip --no-cache-dir install git+https://github.com/NII-cloud-operation/Jupyter-LC_nblineage.git

# Spawner
RUN pip --no-cache-dir install git+https://github.com/jupyterhub/dockerspawner.git \
    requests-unixsocket

# Authenticator
COPY authenticator /tmp/authenticator
RUN pip --no-cache-dir install /tmp/authenticator && \
    rm -rf /tmp/authenticator

ADD cull_idle_servers.py /usr/local/bin/cull_idle_servers.py
ADD add_user.py /usr/local/bin/add_user.py

RUN mkdir /var/jupyterhub/
ADD jupyterhub_config.py /srv/jupyterhub/
