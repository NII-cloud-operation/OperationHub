"""
Mynerva agent isolation: Named Server on a dedicated bridge network
with iptables DOCKER-USER rules for network control.

Loaded via load_subconfig() from jupyterhub_config.py.

Extends CustomDockerSpawner (defined in jupyterhub_config.py) to:
- Override start() for iptables injection after container starts
- Use post_stop_hook for iptables cleanup
- Use pre_spawn_hook for network/mount/env configuration
"""
import asyncio
import ipaddress
import os
import re

import docker

AGENT_NETWORK = os.environ.get('MYNERVA_AGENT_NETWORK', 'mynerva_agent')
AGENT_SERVER_PREFIX = 'mynerva-agent'
AGENT_KEYS_DIR = os.environ.get(
    'MYNERVA_AGENT_KEYS_DIR', '/var/lib/jupyterhub/mynerva-keys'
)
# Auto-detect or use configured host interface for iptables rules.
# Default route's output interface is the most reliable choice.
HOST_IFACE = os.environ.get('MYNERVA_HOST_IFACE', '')

c.JupyterHub.allow_named_servers = True  # noqa: F821


# Grant single-user servers permission to start/stop their own Named Servers.
def _mynerva_token_scopes(spawner):
    username = spawner.user.name
    return [
        f'servers!user={username}',
        f'read:servers!user={username}',
        f'delete:servers!user={username}',
    ]


c.Spawner.server_token_scopes = _mynerva_token_scopes  # noqa: F821


# Track container IPs for iptables cleanup on stop
_agent_ips = {}

_IFACE_RE = re.compile(r'^[a-zA-Z0-9_.-]+$')


def _detect_host_iface():
    """Detect the default route's output interface via a short-lived container."""
    client = docker.from_env()
    output = client.containers.run(
        'alpine',
        command='sh -c "ip route | grep ^default | awk \'{print $5}\'"',
        network_mode='host',
        remove=True,
    )
    return output.decode().strip()


def _get_host_iface():
    """Return the host interface name, auto-detecting if not configured."""
    global HOST_IFACE
    if not HOST_IFACE:
        HOST_IFACE = _detect_host_iface()
    return HOST_IFACE


def _validate_ip(value):
    """Validate and return a strict IP address string."""
    return str(ipaddress.ip_address(value))


def _validate_iface(value):
    """Validate network interface name."""
    if not _IFACE_RE.match(value):
        raise ValueError(f'invalid interface name: {value!r}')
    return value


# --- Firewall helpers (blocking — call via run_in_executor) ---

def _apply_firewall(container_ip, ssh_hosts, iface=None):
    """Inject iptables DOCKER-USER rules via a privileged container."""
    container_ip = _validate_ip(container_ip)
    if iface is None:
        iface = _get_host_iface()
    iface = _validate_iface(iface)
    ssh_hosts = [_validate_ip(h) for h in ssh_hosts]

    # Build a self-contained shell script to avoid quoting issues.
    # DROP must go BEFORE Docker's RETURN rule (which matches all traffic).
    lines = ['set -e', 'apk add --no-cache iptables >/dev/null']

    # Insert DROP before RETURN
    lines.append(
        'RETURN_POS=$(iptables -L DOCKER-USER --line-numbers -n '
        "| awk '/RETURN/{print $1; exit}')"
    )
    lines.append(
        f'iptables -I DOCKER-USER ${{RETURN_POS:-1}} '
        f'-s {container_ip} -o {iface} -j DROP'
    )

    # Insert ACCEPT rules at top (evaluated before DROP)
    for host in reversed(ssh_hosts):
        lines.append(
            f'iptables -I DOCKER-USER -s {container_ip} -o {iface} '
            f'-d {host} -p tcp --dport 22 -j ACCEPT'
        )
    lines.append(
        f'iptables -I DOCKER-USER -s {container_ip} -o {iface} '
        f'-p tcp --dport 443 -j ACCEPT'
    )
    lines.append(
        f'iptables -I DOCKER-USER -s {container_ip} -o {iface} '
        f'-p tcp --dport 53 -j ACCEPT'
    )
    lines.append(
        f'iptables -I DOCKER-USER -s {container_ip} -o {iface} '
        f'-p udp --dport 53 -j ACCEPT'
    )

    script = '\n'.join(lines)
    client = docker.from_env()
    client.containers.run(
        'alpine',
        command=['sh', '-c', script],
        network_mode='host',
        cap_add=['NET_ADMIN'],
        remove=True,
    )


def _remove_firewall(container_ip, iface=None):
    """Remove all DOCKER-USER rules for a given container IP."""
    container_ip = _validate_ip(container_ip)
    if iface is None:
        iface = _get_host_iface()
    iface = _validate_iface(iface)

    # Use iptables-save to find exact rules, then delete each one.
    script = '\n'.join([
        'set -e',
        'apk add --no-cache iptables >/dev/null',
        f'iptables-save -t filter | grep "DOCKER-USER.*-s {container_ip}.*-o {iface}" | '
        'sed "s/^-A /-D /" | '
        'while IFS= read -r rule; do iptables -t filter $rule; done',
        'true',
    ])
    client = docker.from_env()
    client.containers.run(
        'alpine',
        command=['sh', '-c', script],
        network_mode='host',
        cap_add=['NET_ADMIN'],
        remove=True,
    )


def _get_container_ip(object_id):
    """Get the container IP on the agent network."""
    client = docker.from_env()
    container = client.containers.get(object_id)
    return container.attrs['NetworkSettings']['Networks'][AGENT_NETWORK]['IPAddress']


# --- Extend DockerSpawner with iptables in start() ---
#
# CustomDockerSpawner (defined in jupyterhub_config.py) is not accessible
# from load_subconfig scope, and c.JupyterHub.spawner_class returns a
# LazyConfigValue. We inherit from DockerSpawner directly and reproduce
# the get_args customisation from CustomDockerSpawner.

from dockerspawner import DockerSpawner


class MynervaDockerSpawner(DockerSpawner):
    def get_args(self):
        args = super().get_args()
        # Same as CustomDockerSpawner in jupyterhub_config.py
        args.append(self.format_string(
            '--ServerApp.root_dir=/home/{username}/notebooks'
        ))
        return args
    async def start(self):
        result = await super().start()

        if not self.name.startswith(AGENT_SERVER_PREFIX):
            return result

        loop = asyncio.get_event_loop()
        container_ip = await loop.run_in_executor(
            None, _get_container_ip, self.object_id
        )
        ssh_hosts = self.user_options.get('ssh_hosts', [])
        await loop.run_in_executor(
            None, _apply_firewall, container_ip, ssh_hosts
        )
        _agent_ips[self.name] = container_ip
        self.log.info(
            'Mynerva agent firewall applied: ip=%s ssh_hosts=%s',
            container_ip, ssh_hosts
        )

        return result


c.JupyterHub.spawner_class = MynervaDockerSpawner  # noqa: F821


# --- pre_spawn_hook: network + mounts + env ---

_original_pre_spawn_hook = c.Spawner.pre_spawn_hook  # noqa: F821


def mynerva_pre_spawn_hook(spawner):
    if callable(_original_pre_spawn_hook):
        _original_pre_spawn_hook(spawner)

    if not spawner.name.startswith(AGENT_SERVER_PREFIX):
        return

    username = spawner.user.name
    spawner.network_name = AGENT_NETWORK
    spawner.environment['MYNERVA_AGENT_MODE'] = '1'

    # Overlay .ssh with agent-specific keys (keeps all base mounts intact)
    spawner.mounts.append({
        'target': f'/home/{username}/.ssh',
        'source': AGENT_KEYS_DIR,
        'type': 'bind',
        'read_only': True,
    })


c.Spawner.pre_spawn_hook = mynerva_pre_spawn_hook  # noqa: F821


# --- post_stop_hook: remove iptables rules ---

_original_post_stop_hook = c.Spawner.post_stop_hook  # noqa: F821


async def mynerva_post_stop_hook(spawner):
    if callable(_original_post_stop_hook):
        result = _original_post_stop_hook(spawner)
        if asyncio.iscoroutine(result):
            await result

    if spawner.name not in _agent_ips:
        return

    container_ip = _agent_ips.pop(spawner.name)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _remove_firewall, container_ip)
    spawner.log.info(
        'Mynerva agent firewall removed: ip=%s', container_ip
    )


c.Spawner.post_stop_hook = mynerva_post_stop_hook  # noqa: F821
