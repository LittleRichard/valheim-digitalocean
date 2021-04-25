import getpass
import time

import digitalocean
import yaml
from paramiko import SSHClient, AutoAddPolicy

with open('config.yml') as file:
    config_data = yaml.full_load(file)

API_KEY = config_data.get('api_key')
assert API_KEY, 'no digital ocean API key specified'

IMAGE_BASE_NAME = config_data.get('snapshot_name')
assert IMAGE_BASE_NAME, 'no snap name specified'

SNAPS_TO_KEEP = config_data.get('snaps_to_keep')
assert SNAPS_TO_KEEP, 'must keep 1 snap'

manager = digitalocean.Manager(token=API_KEY)

valheim_droplet = None
for droplet in manager.get_all_droplets():
    print(f'Scanning {droplet.name:40s} | {droplet.ip_address:16s} | {droplet.status}')

    if droplet.name.startswith(IMAGE_BASE_NAME) and droplet.status == 'active':
        valheim_droplet = droplet

if valheim_droplet is None:
    print('No droplet found, nothing to stop.  Exiting')
    exit(0)

LOCAL_SSH_PASSWORD = getpass.getpass(prompt='Enter your admin password to access ssh: ')

ssh_client = SSHClient()
ssh_client.load_system_host_keys()
ssh_client.set_missing_host_key_policy(AutoAddPolicy())
ssh_client.connect(passphrase=LOCAL_SSH_PASSWORD,
                   hostname=valheim_droplet.ip_address,
                   username='root')
try:
    command = """
        cd valheim-digitalocean && \
        docker exec -i valheim bash -c "cd ../valheim ; odin stop" && \
        sleep 10 && \
        docker-compose down
    """

    (stdin, stdout, stderr) = ssh_client.exec_command(command)
    print('\nserver stdout (wait for it to finish)')
    print(''.join(stdout.readlines()))
finally:
    ssh_client.close()

print('droplet powering down to take snapshot. '
      'This will take a while...')
snap_name = IMAGE_BASE_NAME + '-' + str(int(time.time()))
snap_action = valheim_droplet.take_snapshot(snap_name,
                                            return_dict=False,
                                            power_off=True)
snap_action.wait()

print('snapshot is processing, cleaning up old snapshots')
snapshots = sorted(
    (x for x in manager.get_droplet_snapshots()
     if x.name.startswith(IMAGE_BASE_NAME)),
    key=lambda x: x.created_at
)
print(f'Found {len(snapshots)} snapshots')
if len(snapshots) > SNAPS_TO_KEEP:
    for snap in snapshots[:-1*SNAPS_TO_KEEP]:
        print(f'destroying snapshot {snap}')
        snap.destroy()

valheim_droplet.load()
print(f'finished snapshot, droplet status: {valheim_droplet.status}')

print('Destroying droplet')
valheim_droplet.destroy()
