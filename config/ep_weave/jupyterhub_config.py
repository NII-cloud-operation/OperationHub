import os
from jupyterhub_oidcp import configure_jupyterhub_oidcp

c.JupyterHub.load_roles = [
    {
        'name': 'user',
        'scopes': ['self', 'access:services'],
    }
]

server_name = os.environ['SERVER_NAME']

configure_jupyterhub_oidcp(
    c,
    base_url=f"https://{server_name}/",
    internal_base_url="http://jupyterhub:8000",
    debug=True,
    services=[
        {
            "oauth_client_id": os.environ['EP_WEAVE_OAUTH_CLIENT_ID'],
            "api_token": os.environ['EP_WEAVE_OAUTH_CLIENT_SECRET'],
            "redirect_uris": [f"https://{server_name}/services/ep_weave/ep_openid_connect/callback"],
        }
    ],
    oauth_client_allowed_scopes=None,
    vault_path="./tmp/jupyterhub_oid/.vault",
)

c.JupyterHub.services.append(
    {
        'name': 'ep_weave',
        'admin': False,
        'url': f'http://ep-weave-etherpad-proxy',
    }
)
