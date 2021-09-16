import time

from paramiko import SSHClient, AutoAddPolicy

from utils import get_curr_droplet, exec_ssh_and_return_output


def stop_server(manager, image_base_name):
    valheim_droplet = get_curr_droplet(manager, image_base_name)
    if valheim_droplet is None:
        print('No droplet found, cannot stop server.')
        return

    ssh_client = SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    try:
        ssh_client.connect(hostname=valheim_droplet.ip_address,
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


def stop_and_snapshot_droplet(manager, image_base_name):
    try:
        valheim_droplet = get_curr_droplet(manager, image_base_name)
        if valheim_droplet is None:
            print('No droplet found, cannot stop droplet.')
            return

        snap_name = image_base_name + '-' + str(int(time.time()))
        snap_action = valheim_droplet.take_snapshot(snap_name,
                                                    return_dict=False,
                                                    power_off=True)
        snap_action.wait()
    finally:
        print('Done stopping server and snapshotting. If this completed '
              'without error, you can proceed to destroy the droplet. \n'
              'HOWEVER if there was an error, you will need to wait for the'
              'snapshot to complete before destroying. Use other commands'
              'to see if your snapshot has been created yet.')


def destroy_droplet(manager, image_base_name, wait_first=True):
    valheim_droplet = get_curr_droplet(manager, image_base_name)
    if valheim_droplet is None:
        print('No droplet found, cannot destroy droplet.')
        return

    if valheim_droplet.status != 'off':
        print(f'Cannot destroy droplet with status {valheim_droplet.status}')

    if wait_first:
        print(f'Found droplet {valheim_droplet}, destroying in 10sec... '
              f'Ctrl-C to cancel')
        time.sleep(10)

    valheim_droplet.destroy()
