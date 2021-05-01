import getpass

import digitalocean
import yaml
from paramiko import SSHClient, AutoAddPolicy

from utils import get_curr_droplet, get_newest_snap, wait_for_active_droplet, \
    exec_ssh_and_return_output

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

manager = digitalocean.Manager(token=API_KEY)

my_droplet = get_curr_droplet(manager, IMAGE_BASE_NAME)

if my_droplet is None:
    valheim_snap = get_newest_snap(manager, IMAGE_BASE_NAME)
    assert valheim_snap, f'could not find snapshot matching {IMAGE_BASE_NAME}'

    print(f'No droplet running, creating one from snapshot {valheim_snap.name}')

    my_droplet = digitalocean.Droplet(token=API_KEY,
                                      name=valheim_snap.name,
                                      region=REGION,
                                      image=valheim_snap.id,
                                      size_slug=SIZE_SLUG,
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
    user_input = input(
        'Would you like to try to start the game server? Enter "Y" if so: ')
    if user_input != "Y":
        print('Exiting...')
        exit()

print('Droplet is ready, updating & starting valheim server. '
      'This may take several minutes...')

LOCAL_SSH_PASSWORD = getpass.getpass(
    prompt='Enter your admin password to access ssh: ')

ssh_client = SSHClient()
ssh_client.load_system_host_keys()
ssh_client.set_missing_host_key_policy(AutoAddPolicy())

try:
    ssh_client.connect(passphrase=LOCAL_SSH_PASSWORD,
                       hostname=my_droplet.ip_address,
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
finally:
    ssh_client.close()

print(f'\n**\nServer ready at IP: {my_droplet.ip_address}\n**\n')
