c.JupyterHub.services.append(
    {
        'name': 'jenkins',
        'admin': False,
        'url': f'http://jenkins-proxy/',
    }
)
