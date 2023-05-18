service_name  = 'solr'

c.JupyterHub.services.append(
    {
        'name': service_name,
        'admin': True,
        'url': f'http://nbsearch-{service_name}-proxy',
    }
)
