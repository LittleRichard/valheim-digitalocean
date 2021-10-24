import cmd2
import sys
import time

import digitalocean
import yaml

from start_server import create_droplet_from_latest_snapshot, start_server
from stop_server import stop_server, stop_and_snapshot_droplet, destroy_droplet
from utils import get_curr_droplet, cull_old_snapshots

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
assert SNAPS_TO_KEEP, 'must keep 1 snap'


class Valhalla(cmd2.Cmd):
    MANAGER = digitalocean.Manager(token=API_KEY)

    def do_create_droplet(self, args):
        create_droplet_from_latest_snapshot(
            Valhalla.MANAGER,
            API_KEY,
            IMAGE_BASE_NAME,
            SIZE_SLUG,
            REGION
        )

    def do_start_server(self, args):
        start_server(Valhalla.MANAGER, IMAGE_BASE_NAME)

    def do_create_droplet_and_start_server(self, args):
        print('Creating droplet from latest snapshot')
        create_droplet_from_latest_snapshot(
            Valhalla.MANAGER,
            API_KEY,
            IMAGE_BASE_NAME,
            SIZE_SLUG,
            REGION
        )
        
        print('Droplet ready, waiting a few seconds for SSH')
        time.sleep(10)

        print('Starting Valheim server')
        start_server(Valhalla.MANAGER, IMAGE_BASE_NAME)

    def do_list_snapshots(self, args):
        snapshots = sorted(
            (x for x in Valhalla.MANAGER.get_droplet_snapshots()
             if x.name.startswith(IMAGE_BASE_NAME)),
            key=lambda x: x.created_at
        )
        for snap in snapshots:
            print(f'Snapshot {snap} created at {snap.created_at} UTC')

    def do_show_droplet(self, args):
        valheim_droplet = get_curr_droplet(Valhalla.MANAGER, IMAGE_BASE_NAME)
        if valheim_droplet is None:
            print('No droplet found.')

    def do_stop_server(self, args):
        stop_server(Valhalla.MANAGER, IMAGE_BASE_NAME)

    def do_stop_and_snapshot_droplet(self, args):
        stop_and_snapshot_droplet(Valhalla.MANAGER, IMAGE_BASE_NAME)

    def do_destroy_droplet(self, args):
        destroy_droplet(Valhalla.MANAGER, IMAGE_BASE_NAME)

    def do_cull_old_snapshots(self, args):
        cull_old_snapshots(Valhalla.MANAGER, IMAGE_BASE_NAME, SNAPS_TO_KEEP)

    def do_stop_snapshot_cull_destroy(self, args):
        print('Stopping Valheim server')
        stop_server(Valhalla.MANAGER, IMAGE_BASE_NAME)

        print('Stopping droplet and snapshotting it')
        print('*** This may take 20-30min!!')
        stop_and_snapshot_droplet(Valhalla.MANAGER, IMAGE_BASE_NAME)

        print('Culling old snapshots')
        cull_old_snapshots(Valhalla.MANAGER, IMAGE_BASE_NAME, SNAPS_TO_KEEP)

        print('Destroying droplet')
        destroy_droplet(Valhalla.MANAGER, IMAGE_BASE_NAME, wait_first=False)

    def do_quit(self, args):
        print('\nSee you in Valhalla...\n')
        return super(Valhalla, self).do_quit(args)


if __name__ == '__main__':
    print("""
    Enter 'help' to see commands, and 'quit' to exit
    
    This tool assumes you've already fully populated the file: config.yml
    """)

    app = Valhalla()
    app.prompt = "To Valhalla>  "
    sys.exit(app.cmdloop())
