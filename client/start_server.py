import digitalocean
import yaml

with open('config.yml') as file:
    config_data = yaml.full_load(file)

DO_TOKEN = config_data.get('API_KEY')
assert DO_TOKEN, 'no digital ocean API key specified'

manager = digitalocean.Manager(token=DO_TOKEN)
my_droplets = manager.get_all_droplets()
print(my_droplets)

