import getpass
import time

import digitalocean
import yaml
from paramiko import SSHClient, AutoAddPolicy

from utils import get_curr_droplet, exec_ssh_and_return_output

with open('config.yml') as file:
    config_data = yaml.full_load(file)

API_KEY = config_data.get('api_key')
assert API_KEY, 'no digital ocean API key specified'

IMAGE_BASE_NAME = config_data.get('snapshot_name')
assert IMAGE_BASE_NAME, 'no snap name specified'

SNAPS_TO_KEEP = config_data.get('snaps_to_keep')
assert SNAPS_TO_KEEP, 'must keep 1 snap'

manager = digitalocean.Manager(token=API_KEY)

valheim_droplet = get_curr_droplet(manager, IMAGE_BASE_NAME)
if valheim_droplet is None:
    print('No droplet found, nothing to stop.  Exiting')
    exit(0)

LOCAL_SSH_PASSWORD = getpass.getpass(
    prompt='Enter your admin password to access ssh: ')

ssh_client = SSHClient()
ssh_client.load_system_host_keys()
ssh_client.set_missing_host_key_policy(AutoAddPolicy())
try:
    ssh_client.connect(passphrase=LOCAL_SSH_PASSWORD,
                       hostname=valheim_droplet.ip_address,
                       username='root')

    command = """
        cd valheim-digitalocean && \
        docker exec -i valheim bash -c "cd ../valheim ; odin stop" && \
        sleep 5 && \
        docker-compose down
    """

    print('Stopping server, may take a minute or two.')
    result = exec_ssh_and_return_output(ssh_client, command)
    print(result)
finally:
    ssh_client.close()

print('Stopping droplet to take a snapshot. '
      'This will take several minutes, please wait...')
snap_name = IMAGE_BASE_NAME + '-' + str(int(time.time()))
snap_action = valheim_droplet.take_snapshot(snap_name,
                                            return_dict=False,
                                            power_off=True)
snap_action.wait()

print('Snapshot complete, game data is backed up. Cleaning old snapshots.')
snapshots = sorted(
    (x for x in manager.get_droplet_snapshots()
     if x.name.startswith(IMAGE_BASE_NAME)),
    key=lambda x: x.created_at
)
if len(snapshots) > SNAPS_TO_KEEP:
    print(f'Found {len(snapshots)} snapshots, culling old ones')
    for snap in snapshots[:-1*SNAPS_TO_KEEP]:
        print(f'*** destroying snapshot {snap}')
        snap.destroy()

print('Destroying droplet')
valheim_droplet.destroy()
