import cmd2
import sys
import time

import digitalocean
import yaml

from server_utils import (droplet_create_from_latest_snapshot, server_start,
                          server_stop, droplet_stop_and_snapshot, droplet_destroy)
from utils import get_curr_droplet, snapshot_cull_old

with open('config.yml') as file:
    config_data = yaml.full_load(file)

API_KEY = config_data.get('api_key')
assert API_KEY, 'no digital ocean API key specified'

IMAGE_BASE_NAME = config_data.get('snapshot_name')
assert IMAGE_BASE_NAME, 'no snap name specified'

SIZE_SLUG = config_data.get('size_slug')
assert SIZE_SLUG, 'no size slug specified'

REGION = config_data.get('region')
assert REGION, 'no region specified'

SNAPS_TO_KEEP = config_data.get('snaps_to_keep')
assert SNAPS_TO_KEEP >= 2, 'must keep at least 2 snaps, safety first'


class Valhalla(cmd2.Cmd):
    MANAGER = digitalocean.Manager(token=API_KEY)

    def do_droplet_create(self, args):
        droplet_create_from_latest_snapshot(
            Valhalla.MANAGER,
            API_KEY,
            IMAGE_BASE_NAME,
            SIZE_SLUG,
            REGION
        )

    def do_server_start(self, args):
        server_start(Valhalla.MANAGER, IMAGE_BASE_NAME)

    def do_snapshot_list(self, args):
        snapshots = sorted(
            (x for x in Valhalla.MANAGER.get_droplet_snapshots()
             if x.name.startswith(IMAGE_BASE_NAME)),
            key=lambda x: x.created_at
        )
        for snap in snapshots:
            print(f'Snapshot {snap} created at {snap.created_at} UTC')

    def do_droplet_show(self, args):
        valheim_droplet = get_curr_droplet(Valhalla.MANAGER, IMAGE_BASE_NAME)
        if valheim_droplet is None:
            print('No droplet found.')

    def do_server_stop(self, args):
        server_stop(Valhalla.MANAGER, IMAGE_BASE_NAME)

    def do_droplet_stop_and_snapshot(self, args):
        droplet_stop_and_snapshot(Valhalla.MANAGER, IMAGE_BASE_NAME)

    def do_droplet_destroy(self, args):
        droplet_destroy(Valhalla.MANAGER, IMAGE_BASE_NAME)

    def do_snapshot_cull_old(self, args):
        snapshot_cull_old(Valhalla.MANAGER, IMAGE_BASE_NAME, SNAPS_TO_KEEP)

    def do_full_up(self, args):
        print('Creating droplet from latest snapshot')
        droplet_create_from_latest_snapshot(
            Valhalla.MANAGER,
            API_KEY,
            IMAGE_BASE_NAME,
            SIZE_SLUG,
            REGION
        )

        print('Droplet ready, waiting a few seconds for SSH')
        time.sleep(10)

        print('Starting Valheim server')
        server_start(Valhalla.MANAGER, IMAGE_BASE_NAME)

    def do_full_down(self, args):
        print('Stopping Valheim server')
        server_stop(Valhalla.MANAGER, IMAGE_BASE_NAME)

        print('Stopping droplet and snapshotting it')
        print('*** This may take 20-30min!!')
        droplet_stop_and_snapshot(Valhalla.MANAGER, IMAGE_BASE_NAME)

        print('Culling old snapshots')
        snapshot_cull_old(Valhalla.MANAGER, IMAGE_BASE_NAME, SNAPS_TO_KEEP)

        print('Destroying droplet')
        droplet_destroy(Valhalla.MANAGER, IMAGE_BASE_NAME, wait_first=False)

    def do_quit(self, args):
        print('\nSee you in Valhalla...\n')
        return super(Valhalla, self).do_quit(args)


if __name__ == '__main__':
    print("""
    This tool assumes you've already fully populated the file: config.yml
    
    Enter 'help' to see commands, and 'quit' to exit
    """)

    app = Valhalla()
    app.prompt = "To Valhalla>  "
    sys.exit(app.cmdloop())
