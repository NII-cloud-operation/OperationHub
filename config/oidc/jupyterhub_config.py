from distutils.util import strtobool
import os

from jupyterhub_oidcp import configure_jupyterhub_oidcp

c.JupyterHub.load_roles = [
    {
        'name': 'user',
        'scopes': ['self', 'access:services'],
    }
]

server_name = os.environ['SERVER_NAME']

oidc_services = []
enable_ep_weave = os.environ.get('EP_WEAVE_ENABLE_OIDC_SERVICE', None)
if enable_ep_weave is not None and bool(strtobool(enable_ep_weave)):
    oidc_services.append({
        "oauth_client_id": os.environ['EP_WEAVE_OAUTH_CLIENT_ID'],
        "api_token": os.environ['EP_WEAVE_OAUTH_CLIENT_SECRET'],
        "redirect_uris": [f"https://{server_name}/services/ep_weave/ep_openid_connect/callback"],
    })

enable_nbsearch = os.environ.get('NBSEARCHDB_ENABLE_OIDC_SERVICE', None)
if enable_nbsearch is not None and bool(strtobool(enable_nbsearch)):
    oidc_services.append({
        "oauth_client_id": os.environ['NBSEARCHDB_OAUTH_CLIENT_ID'],
        "api_token": os.environ['NBSEARCHDB_OAUTH_CLIENT_SECRET'],
        "redirect_uris": [f"https://{server_name}/services/solr/oauth2/callback"],
    })

enable_jenkins = os.environ.get('JENKINS_ENABLE_OIDC_SERVICE', None)
if enable_jenkins is not None and bool(strtobool(enable_jenkins)):
    oidc_services.append({
        "oauth_client_id": os.environ['JENKINS_OAUTH_CLIENT_ID'],
        "api_token": os.environ['JENKINS_OAUTH_CLIENT_SECRET'],
        "redirect_uris": [f"https://{server_name}/services/jenkins/securityRealm/finishLogin"],
    })

if len(oidc_services) > 0:
    configure_jupyterhub_oidcp(
        c,
        issuer="http://jupyterhub:8000/services/oidcp/internal/",
        base_url=f"https://{server_name}/",
        internal_base_url="http://jupyterhub:8000",
        debug=True,
        services=oidc_services,
        oauth_client_allowed_scopes=None,
        vault_path="./tmp/jupyterhub_oid/.vault",
        admin_email_pattern="{uid}@admin.jupyterhub",
        user_email_pattern="{uid}@user.jupyterhub",
    )
