import digitalocean
from paramiko import SSHClient, AutoAddPolicy

from utils import (get_curr_droplet, get_newest_snap, wait_for_active_droplet,
                   exec_ssh_and_return_output)


def create_droplet_from_latest_snapshot(manager, api_key, image_base_name,
                                        size_slug, region):

    my_droplet = get_curr_droplet(manager, image_base_name)

    if my_droplet is None:
        valheim_snap = get_newest_snap(manager, image_base_name)
        assert valheim_snap, (
            f'could not find snapshot matching {image_base_name}')

        print(f'No droplet running, creating one '
              f'from snapshot {valheim_snap.name}')

        my_droplet = digitalocean.Droplet(token=api_key,
                                          name=valheim_snap.name,
                                          region=region,
                                          image=valheim_snap.id,
                                          size_slug=size_slug,
                                          backups=False,
                                          monitoring=True,
                                          ssh_keys=manager.get_all_sshkeys())
        my_droplet.create()

        # this function is a generator of status messages, and will
        # raise an error if it exceeds the maximum wait time.
        for status_msg in wait_for_active_droplet(my_droplet):
            print(status_msg)
    else:
        print(f'Droplet already exists at {my_droplet.ip_address}')
        for status_msg in wait_for_active_droplet(my_droplet):
            print(status_msg)

    print('Droplet is ready, you can now start the valheim server.')


def start_server(manager, image_base_name):
    valheim_droplet = get_curr_droplet(manager, image_base_name)
    if valheim_droplet is None:
        print(f'No droplet found with name matching {image_base_name}')
        return

    ssh_client = SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())

    try:
        ssh_client.connect(hostname=valheim_droplet.ip_address,
                           username='root')

        update_and_setup_cmd = """
        cd valheim-digitalocean && \
        git pull && \
        cd server && \
        docker system prune --force && \
        echo "Done with update/setup"
        """
        output = exec_ssh_and_return_output(ssh_client, update_and_setup_cmd)
        print(output)

        start_container_cmd = """
        cd valheim-digitalocean/server && \
        docker-compose up -d && \
        echo "Starting containers"
        """
        output = exec_ssh_and_return_output(ssh_client, start_container_cmd)
        print(output)

        start_game_server_cmd = """
        docker exec -i valheim bash -c "cd ../valheim && odin update && odin start"
        """
        output = exec_ssh_and_return_output(ssh_client, start_game_server_cmd)
        print(output)
    except Exception:
        print("""
        This tool assumes you've successfully done an SSH handshake with the 
        server, which likely requires super-user permissions.  
        
        If you get SSH errors, try executing in a shell first:
        ssh root@<ip address of an already running server>
        
        If you get "Unable to connect to port 22", wait a couple minutes and
        try starting the server again.
        """)
        raise
    finally:
        ssh_client.close()

    print(f'\n**\nServer started, but give it 1min to be '
          f'ready to accept connections.\n'
          f'IP: {valheim_droplet.ip_address}\n**\n')

