import json

from jupyterhub.auth import PAMAuthenticator
from jupyterhub.utils import maybe_future

import requests_unixsocket


class OphubPAMAuthenticator(PAMAuthenticator):

    def mount_nbdir(self, username):
        session = requests_unixsocket.Session()
        r = session.post('http+unix://%2Fvar%2Frun%2Fjupyterhub%2Fophubuser.sock/mount/{}'.format(username))
        self.log.info('Mount user notebook dir: %s', json.dumps(r.json()))

    async def add_user(self, user):
        await maybe_future(super().add_user(user))

        self.mount_nbdir(user.name)

    async def is_admin(self, handler, authentication):
        admin_status = await maybe_future(super().is_admin(handler, authentication))

        # This is the workaround for preventing to override admin status in the user database
        if admin_status is not None and admin_status == False:
            admin_status = None
        return admin_status

