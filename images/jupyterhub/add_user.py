import json

from tornado.log import app_log
from tornado.options import parse_command_line

import requests_unixsocket


def create_user(username):
    session = requests_unixsocket.Session()
    r = session.post('http+unix://%2Fvar%2Frun%2Fjupyterhub%2Frestuser.sock/{}'.format(username))
    app_log.info('Call restuser: %s', json.dumps(r.json()))

def mount_nbdir(username):
    session = requests_unixsocket.Session()
    r = session.post('http+unix://%2Fvar%2Frun%2Fjupyterhub%2Fophubuser.sock/mount/{}'.format(username))
    app_log.info('Mount user notebook dir: %s', json.dumps(r.json()))


if __name__ == '__main__':
    args = parse_command_line()

    assert len(args) > 0
    username = args[0]

    create_user(username)
#    mount_nbdir(username)

