import os
import sys
import subprocess

from datetime import datetime
from dateutil.tz import tzlocal

from nblineage.tracking_server import TrackingServer

c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.ip = '0.0.0.0'
c.JupyterHub.port = 8000
c.JupyterHub.hub_connect_ip = 'jupyterhub'

c.JupyterHub.db_url = 'sqlite:////srv/jupyterhub/data/jupyterhub.sqlite'

# init server signature file
tracking_server = TrackingServer()
tracking_server.server_signature_file = '/srv/jupyterhub/data/server_signature'
tracking_server.server_signature

# shared directories
users_host_dir = os.environ['USERS_DIR']
shared_host_dir = os.environ['SHARED_DIR']
shared_dir = '/var/jupyterhub/share'
os.chmod(shared_dir, 0o0777)
subprocess.check_output([
    '/usr/bin/setfacl', '-d', '-m', 'group::rwx,other:rx', shared_dir
])

# Spawner
c.JupyterHub.spawner_class = 'docker'
c.DockerSpawner.use_internal_hostname = True
c.DockerSpawner.image = os.environ.get('SINGLE_USER_IMAGE', 'niicloudoperation/notebook')
c.DockerSpawner.network_name = os.environ['BACKEND_NETWORK']
c.DockerSpawner.notebook_dir = '/home/{username}/notebooks'
c.DockerSpawner.volumes = {
    '/home/{username}': '/home/{username}',
    shared_host_dir: '/home/{username}/notebooks/share'
}
server_signature_host_path = os.environ['SERVER_SIGNATURE_HOST_PATH']
c.DockerSpawner.read_only_volumes = {
    users_host_dir: '/home/{username}/notebooks/users',
    server_signature_host_path: '/var/lib/jupyter/server_signature',
}
c.DockerSpawner.extra_create_kwargs = {
    'user': 0
}
c.DockerSpawner.remove = True
c.Spawner.cmd = '/usr/local/bin/start-notebook.sh'

def get_username(spawner):
    return spawner.user.name

def get_uid(spawner):
    import pwd
    return str(pwd.getpwnam(spawner.user.name).pw_uid)

tz = datetime.now(tzlocal()).tzname()

c.Spawner.environment = {
    'lc_nblineage_server_signature_path': '/var/lib/jupyter/server_signature',
    'NB_USER': get_username,
    'NB_UID': get_uid,
    'GRANT_SUDO': 'yes',
    'TZ': tz
}

lc_wrapper_fluentd_host = os.environ.get('LC_WRAPPER_FLUENTD_HOST')
if lc_wrapper_fluentd_host is not None and lc_wrapper_fluentd_host == '':
    lc_wrapper_fluentd_host = None
if lc_wrapper_fluentd_host is not None:
    lc_wrapper_fluentd_port = int(os.environ.get('LC_WRAPPER_FLUENTD_PORT', '24224'))
    c.Spawner.environment.update({
        'lc_wrapper_fluentd_host': lc_wrapper_fluentd_host,
	'lc_wrapper_fluentd_port': lc_wrapper_fluentd_port,
    })

def mount_user_nbdir(spawner):
    spawner.authenticator.mount_nbdir(spawner.user.name)

c.Spawner.pre_spawn_hook = mount_user_nbdir

# Authenticator
c.JupyterHub.authenticator_class = 'ophub-pam'
c.LocalAuthenticator.create_system_users = True
c.LocalAuthenticator.add_user_cmd = [sys.executable, '/usr/local/bin/add_user.py']
c.PAMAuthenticator.admin_groups = {'wheel'}
c.Authenticator.blacklist = {'root'}

# debug
debug = os.environ.get('DEBUG', 'no')
if debug == '1' or debug == 'yes':
    c.JupyterHub.log_level = 'DEBUG'
    c.Spawner.debug = True

# logo
c.JupyterHub.logo_file = '/var/jupyterhub/logo.png'

# services
services = []

cull_server = os.environ.get('CULL_SERVER', 'no')
if cull_server == '1' or cull_server == 'yes':
    cull_server_idle_timeout = int(os.environ.get('CULL_SERVER_IDLE_TIMEOUT', '3600'))
    cull_server_max_age = int(os.environ.get('CULL_SERVER_MAX_AGE', '0'))
    cull_server_every = int(os.environ.get('CULL_SERVER_EVERY', '0'))
    if cull_server_idle_timeout > 0:
        services.append(
            {
                'name': 'cull-idle',
                'admin': True,
                'command': [sys.executable,
                            '/usr/local/bin/cull_idle_servers.py',
                            '--timeout={}'.format(str(cull_server_idle_timeout)),
                            '--max-age={}'.format(str(cull_server_max_age)),
                            '--cull-every={}'.format(str(cull_server_every))],
            }
        )

c.JupyterHub.services = services

