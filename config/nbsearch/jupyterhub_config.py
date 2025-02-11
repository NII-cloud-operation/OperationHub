service_name  = 'solr'

c.JupyterHub.services.append(
    {
        'name': service_name,
        'url': f'http://nbsearch-{service_name}-proxy',
    }
)
