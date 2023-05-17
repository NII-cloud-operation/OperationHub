service_name = 'solr'

c.JupyterHub.services.append(
    {
        'name': service_name,
        'admin': True,
        'url': "http://nbsearch-solr-proxy",
    }
)
