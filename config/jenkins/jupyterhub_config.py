from distutils.util import strtobool
import os

from jupyterhub_oidcp import configure_jupyterhub_oidcp

# Admin users can access the Jenkins service
# because the `access:services!service=oidcp-jenkins` scope is required
# To access the Jenkins service by non-admin users,
# the `access:services!service=oidcp-jenkins` scope should be added to the user's role

server_name = os.environ['SERVER_NAME']

c.JupyterHub.services.append(
    {
        'name': 'jenkins',
        'url': f'http://jenkins-proxy/',
    }
)

oidc_services = []

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
        port=8889,
        service_name="oidcp-jenkins",
        issuer="http://jupyterhub:8000/services/oidcp-jenkins/internal/",
        base_url=f"https://{server_name}/",
        internal_base_url="http://jupyterhub:8000",
        debug=True,
        services=oidc_services,
        vault_path="./tmp/jupyterhub_oid/.jenkins.vault",
        admin_email_pattern="{uid}@admin.jupyterhub",
        user_email_pattern="{uid}@user.jupyterhub",
    )
