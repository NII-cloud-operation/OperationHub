c.JupyterHub.services.append(
    {
        'name': 'ep_weave',
        'admin': False,
        'url': f'http://ep-weave-etherpad-proxy',
    }
)
