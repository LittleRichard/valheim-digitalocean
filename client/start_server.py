import time

import digitalocean
import yaml
from paramiko import SSHClient, AutoAddPolicy

with open('config.yml') as file:
    config_data = yaml.full_load(file)

API_KEY = config_data.get('api_key')
assert API_KEY, 'no digital ocean API key specified'

LOCAL_SSH_PASSWORD = config_data.get('local_ssh_password')
assert LOCAL_SSH_PASSWORD, 'no local SSH password'

IMAGE_BASE_NAME = config_data.get('snapshot_name')
assert IMAGE_BASE_NAME, 'no snap name specified'

SIZE_SLUG = config_data.get('size_slug')
assert SIZE_SLUG, 'no size slug specified'

REGION = config_data.get('region')
assert REGION, 'no region specified'

manager = digitalocean.Manager(token=API_KEY)

valheim_droplet = None
for droplet in manager.get_all_droplets():
    print(f'Scanning {droplet.name:40s} | {droplet.ip_address:16s} | {droplet.status}')

    if droplet.name.startswith(IMAGE_BASE_NAME):
        valheim_droplet = droplet

if valheim_droplet is None:
    # go find the snapshot and make a droplet for it
    snapshots = manager.get_droplet_snapshots()
    valheim_snap = None
    for snap in sorted(snapshots, key=lambda x: x.created_at):
        if snap.name.startswith(IMAGE_BASE_NAME):
            print(f'found snap {snap.name} created at {snap.created_at}')
            valheim_snap = snap  # will end with the newest one

    if valheim_snap is None:
        assert False, f'could not find snapshot {IMAGE_BASE_NAME}'

    print(f'no droplet, but found snap. creating from snap {snap.name}')

    valheim_droplet = digitalocean.Droplet(token=API_KEY,
                                           name=snap.name,
                                           region=REGION,
                                           image=snap.id,
                                           size_slug=SIZE_SLUG,
                                           backups=False,
                                           ssh_keys=manager.get_all_sshkeys())
    valheim_droplet.create()
    idx = 0
    max_idx = 100
    sleep_sec = 5
    while True:
        valheim_droplet.load()
        print(f'Status {valheim_droplet.status} | {valheim_droplet.ip_address} '
              f'after {idx * sleep_sec} sec')

        if valheim_droplet.status == 'active':
            time.sleep(sleep_sec)  # give it a second to become ready
            break
        idx += 1
        time.sleep(sleep_sec)

        assert idx != max_idx, 'hit max retries... ruh roh'
else:
    print(f'Droplet already exists at {valheim_droplet.ip_address}, '
          f'not creating one.')

print('Droplet is ready, starting up valheim server. '
      'This may take several minutes...')
ssh_client = SSHClient()
ssh_client.load_system_host_keys()
ssh_client.set_missing_host_key_policy(AutoAddPolicy())
ssh_client.connect(passphrase=LOCAL_SSH_PASSWORD,
                   hostname=valheim_droplet.ip_address,
                   username='root')
try:
    command = """
    cd valheim-digitalocean && \
    git pull && \
    cd server && \
    docker system prune --force && \
    docker-compose up -d && \
    sleep 10 && \
    docker exec -i valheim bash -c "cd ../valheim ; odin start"
    """

    (stdin, stdout, stderr) = ssh_client.exec_command(command)
    print(''.join(stdout.readlines()))
finally:
    ssh_client.close()

print(f'\n**\nVIKING TIME at IP: {valheim_droplet.ip_address}\n**\n')
