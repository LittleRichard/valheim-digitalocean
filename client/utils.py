import time


def get_curr_droplet(manager, image_base_name):
    for droplet in manager.get_all_droplets():
        print(
            f'Scanning {droplet.name:40s} | '
            f'{droplet.ip_address:16s} | '
            f'{droplet.status}')

        if droplet.name.startswith(image_base_name):
            return droplet


def get_newest_snap(manager, image_base_name):
    # go find the snapshot and make a droplet for it
    snapshots = manager.get_droplet_snapshots()
    valheim_snap = None
    for snap in sorted(snapshots, key=lambda x: x.created_at):
        if snap.name.startswith(image_base_name):
            print(f'found snap {snap.name} created at {snap.created_at}')
            valheim_snap = snap  # will end with the newest one

    return valheim_snap


def wait_for_active_droplet(droplet, check_every_sec=5, max_wait_sec=300):
    curr_wait_sec = 0
    while droplet.status != 'active':
        droplet.load()
        yield (f'Status {droplet.status} | {droplet.ip_address} '
               f'after {curr_wait_sec} seconds')

        if droplet.status == 'active':
            return
        curr_wait_sec += check_every_sec

        assert curr_wait_sec < max_wait_sec, (
            f'Waited longer than {max_wait_sec} seconds '
            f'for droplet to be active')

        time.sleep(check_every_sec)


def exec_ssh_and_return_output(ssh_client, command_str):
    (stdin, stdout, stderr) = ssh_client.exec_command(command_str)
    return ''.join(stdout.readlines())
