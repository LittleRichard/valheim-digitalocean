import digitalocean
import yaml

with open('config.yml') as file:
    config_data = yaml.full_load(file)

DO_TOKEN = config_data.get('API_KEY')
assert DO_TOKEN, 'no digital ocean API key specified'

SNAP_NAME = config_data.get('snapshot_name')
assert SNAP_NAME, 'no snap name specified'

manager = digitalocean.Manager(token=DO_TOKEN)

valheim_droplet = None
for droplet in manager.get_all_droplets():
    print(f'Scanning {droplet.name:40s} | {droplet.ip_address:16s} | {droplet.status}')

    if droplet.name == SNAP_NAME:
        valheim_droplet = droplet

if valheim_droplet is None:
    # go find the snapshot and make a droplet for it
    snapshots = manager.get_droplet_snapshots()
    for snap in snapshots:
        if snap.name == SNAP_NAME:
            valheim_snap = snap
            break
    else:
        assert False, f'could not find snapshot {SNAP_NAME}'

    print('no droplet, but found snap. creating from snap')

    valheim_droplet = digitalocean.Droplet(token=DO_TOKEN,
                                           name=SNAP_NAME,
                                           # region='nyc2', # New York 2
                                           image=snap.id, # Ubuntu 20.04 x64
                                           # size_slug='s-1vcpu-1gb',  # 1GB RAM, 1 vCPU
                                           backups=False)
    valheim_droplet.create()
    print('Done creating, waiting for start')

