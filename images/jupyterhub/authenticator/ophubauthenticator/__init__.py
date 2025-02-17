import json
import aiohttp
from urllib.parse import urljoin

from traitlets import Unicode

from jupyterhub.auth import PAMAuthenticator
from jupyterhub.utils import maybe_future


class OphubPAMAuthenticator(PAMAuthenticator):

    ophubuser_socket_path = Unicode(
        "/var/run/jupyterhub/ophubuser.sock",
        config=True,
        help="Path to the Unix socket for the user service"
    )

    ophubuser_base_url = Unicode(
        "http://localhost/mount/",
        config=True,
        help="Base URL for the user service"
    )

    async def mount_nbdir(self, username):
        url = urljoin(self.ophubuser_base_url, username)
        connector = aiohttp.UnixConnector(path=self.ophubuser_socket_path)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(url) as resp:
                response = await resp.json(content_type=None)
                self.log.info('Mount user notebook dir: %s', json.dumps(response))

    async def add_user(self, user):
        await maybe_future(super().add_user(user))

        await self.mount_nbdir(user.name)

    async def is_admin(self, handler, authentication):
        admin_status = await maybe_future(super().is_admin(handler, authentication))

        # This is the workaround for preventing to override admin status in the user database
        if admin_status is not None and admin_status == False:
            admin_status = None
        return admin_status

