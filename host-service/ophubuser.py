import json
import os
import pwd
import re
import sys
from subprocess import Popen, PIPE

from tornado import web
from tornado.log import app_log
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.netutil import bind_unix_socket
from tornado.options import define, parse_command_line, options


class BaseHandler(web.RequestHandler):


    def exec_cmd(self, cmd):
        app_log.info("Running %s", cmd)
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        if p.returncode:
            err = err.decode('utf8', 'replace').strip()
            raise web.HTTPError(400, err)
        return (out, err)


class MountHandler(BaseHandler):


    def mount(self, nbdir, mountpoint):
        cmd = ['mount', '--bind', nbdir, mountpoint]
        self.exec_cmd(cmd)

    def ismount(self, mountpoint):
        cmd = ['mount']
        out, err = self.exec_cmd(cmd)
        for line in out.decode('utf8', 'replace').split('\n'):
            m = re.match(r'.+ on {} type.+'.format(re.escape(mountpoint)), line)
            if m:
                return True
        return False

    def get_ugid(self, name):
        user = pwd.getpwnam(name)
        return (user.pw_uid, user.pw_gid)

    def post(self, name):
        nbdir = self.settings['notebookdir'].replace('USERNAME', name)
        mountpoint = os.path.join(self.settings['usersdir'], name)
        if not os.path.exists(mountpoint):
            os.makedirs(mountpoint)
        if not os.path.exists(nbdir):
            os.makedirs(nbdir)
        uid, gid = self.get_ugid(name)
        os.chown(nbdir, uid, gid)
        os.chown(mountpoint, uid, gid)
        if not self.ismount(mountpoint):
            self.mount(nbdir, mountpoint)
        d = {
            'username': name,
            'notebookdir': nbdir,
            'mountpoint': mountpoint
        }
        self.finish(json.dumps(d))


def main():
    define('socket', default='/var/run/ophubuser.sock', help='unix socket path to bind')
    define('usersdir', default='/home/user-notebooks', help='Shared user notebook directory')
    define('notebookdir', default='/home/USERNAME/notebooks',
           help='path of a notebook directory for each user. "USERNAME" will be replaced by the name of user')

    parse_command_line()

    app = web.Application(
        [(r'/mount/([^/]+)', MountHandler)],
        notebookdir=options.notebookdir,
        usersdir=options.usersdir)

    socket = bind_unix_socket(options.socket, mode=0o600)
    server = HTTPServer(app)
    server.add_socket(socket)
    try:
        IOLoop.current().start()
    except KeyboardInterrupt:
        print("\ninterrupted\n", file=sys.stderr)
        return


if __name__ == '__main__':
    main()

