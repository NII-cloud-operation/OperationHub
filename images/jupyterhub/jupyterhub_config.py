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

from dockerspawner import DockerSpawner

class CustomDockerSpawner(DockerSpawner):
    def get_args(self):
        args = super().get_args()
        # WORKAROUND: SingleUserNotebookApp.* preferences are ignored when ServerApp is specified
        args.append(self.format_string('--ServerApp.root_dir=/home/{username}/notebooks'))
        return args

# Spawner
c.JupyterHub.spawner_class = CustomDockerSpawner
c.DockerSpawner.use_internal_hostname = True
c.DockerSpawner.image = os.environ.get('SINGLE_USER_IMAGE', 'niicloudoperation/notebook')
c.DockerSpawner.network_name = os.environ['BACKEND_NETWORK']
c.DockerSpawner.notebook_dir = '/home/{username}/notebooks'
server_signature_host_path = os.environ['SERVER_SIGNATURE_HOST_PATH']
c.DockerSpawner.mounts = [
    {
        'target': '/home/{username}',
        'source': '/home/{username}',
        'type': 'bind',
        'read_only': False,
    },
    {
        'target': '/home/{username}/notebooks/share',
        'source': shared_host_dir,
        'type': 'bind',
        'read_only': False,
    },
    {
        'target': '/home/{username}/notebooks/users',
        'source': users_host_dir,
        'type': 'bind',
        'read_only': True,
        'propagation': 'rslave'
    },
    {
        'target': '/var/lib/jupyter/server_signature',
        'source': server_signature_host_path,
        'type': 'bind',
        'read_only': True,
    }
]
c.DockerSpawner.extra_create_kwargs = {
    'user': 0
}
c.DockerSpawner.remove = True

single_user_mem_limit = os.environ.get('SINGLE_USER_MEM_LIMIT', '').strip()
if single_user_mem_limit:
    c.DockerSpawner.mem_limit = single_user_mem_limit

c.Spawner.cmd = '/usr/local/bin/start-notebook.sh'

notebook_args = []
single_user_default_url = os.environ.get('SINGLE_USER_DEFAULT_URL', '').strip()
if single_user_default_url:
    notebook_args.append(
        '--SingleUserNotebookApp.default_url={}'.format(single_user_default_url))
    # WORKAROUND: SingleUserNotebookApp.* preferences are ignored when ServerApp is specified
    notebook_args.append(
        '--ServerApp.default_url={}'.format(single_user_default_url))
c.Spawner.args = notebook_args

def get_username(spawner):
    return spawner.user.name

def get_uid(spawner):
    import pwd
    return str(pwd.getpwnam(spawner.user.name).pw_uid)

dt = datetime.now(tzlocal())
utc_offset = dt.utcoffset().seconds
utc_offset_str = '{:+.0f}'.format(-utc_offset / 3600) if utc_offset != 0 else ''
tz = dt.tzname() + utc_offset_str

c.Spawner.environment = {
    'lc_nblineage_server_signature_path': '/var/lib/jupyter/server_signature',
    'NB_USER': get_username,
    'NB_UID': get_uid,
    'GRANT_SUDO': 'yes',
    'TZ': tz
}

if 'SINGLE_USER_APP' in os.environ:
    c.Spawner.environment.update({
        'JUPYTERHUB_SINGLEUSER_APP': os.environ['SINGLE_USER_APP']
    })

for key in os.environ.keys():
    if key.startswith('NBSEARCHDB_'):
        c.Spawner.environment[key] = os.environ[key]

def get_nbsearch_basedir(spawner):
    return '/home/{username}/notebooks'.format(username=spawner.user.name)

c.Spawner.environment['NBSEARCHDB_BASE_DIR'] = get_nbsearch_basedir

scrapbox_project_id = os.environ.get('SIDESTICKIES_SCRAPBOX_PROJECT_ID')
scrapbox_cookie_connect_sid = os.environ.get('SIDESTICKIES_SCRAPBOX_COOKIE_CONNECT_SID')
if scrapbox_project_id and scrapbox_cookie_connect_sid:
    c.Spawner.environment.update({
        'SIDESTICKIES_SCRAPBOX_PROJECT_ID': scrapbox_project_id,
        'SIDESTICKIES_SCRAPBOX_COOKIE_CONNECT_SID': scrapbox_cookie_connect_sid
    })

ep_weave_url = os.environ.get('SIDESTICKIES_EP_WEAVE_URL')
ep_weave_api_key = os.environ.get('SIDESTICKIES_EP_WEAVE_API_KEY')
ep_weave_api_url = os.environ.get('SIDESTICKIES_EP_WEAVE_API_URL')
if ep_weave_url:
    c.Spawner.environment.update({
        'SIDESTICKIES_EP_WEAVE_URL': ep_weave_url,
        'SIDESTICKIES_EP_WEAVE_API_KEY': ep_weave_api_key,
        'SIDESTICKIES_EP_WEAVE_API_URL': ep_weave_api_url,
    })

lc_wrapper_fluentd_host = os.environ.get('LC_WRAPPER_FLUENTD_HOST')
if lc_wrapper_fluentd_host is not None and lc_wrapper_fluentd_host == '':
    lc_wrapper_fluentd_host = None
if lc_wrapper_fluentd_host is not None:
    lc_wrapper_fluentd_port = int(os.environ.get('LC_WRAPPER_FLUENTD_PORT', '24224'))
    c.Spawner.environment.update({
        'lc_wrapper_fluentd_host': lc_wrapper_fluentd_host,
	'lc_wrapper_fluentd_port': lc_wrapper_fluentd_port,
    })

for key in os.environ.keys():
    if key.startswith('NBWHISPER_') and os.environ[key]:
        c.Spawner.environment[key] = os.environ[key]

def mount_user_nbdir(spawner):
    spawner.authenticator.mount_nbdir(spawner.user.name)

c.Spawner.pre_spawn_hook = mount_user_nbdir

# Authenticator
c.JupyterHub.authenticator_class = 'ophub-pam'
c.LocalAuthenticator.create_system_users = True
c.LocalAuthenticator.add_user_cmd = [sys.executable, '/usr/local/bin/add_user.py']
c.PAMAuthenticator.admin_groups = set(os.environ.get('ADMIN_GROUPS', '').split())
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

# load additional config files
additional_config_path = os.environ.get('JUPYTERHUB_ADDITIONAL_CONFIG_PATH',
                                        '/jupyterhub_config.d')
if os.path.exists(additional_config_path):
    for filename in sorted(os.listdir(additional_config_path)):
        _, ext = os.path.splitext(filename)
        if ext.lower() != '.py':
            continue
        load_subconfig(os.path.join(additional_config_path, filename))
