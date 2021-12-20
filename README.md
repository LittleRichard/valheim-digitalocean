# valheim-digitalocean
A wrapper around a valheim server and Digital Ocean to make it easy to run a server in the cloud and start/stop it to save money. This has been developed as a convenience and is not bulletproof, so please try to understand what it is doing before blindly using it.  

### thanks to other open source
- for providing docker containers that make running the server simple: https://github.com/mbround18/valheim-docker
- for providing a feature-rich DigitalOcean API in python: https://github.com/koalalorenzo/python-digitalocean

### starting from scratch? How to set up a server
The server is mostly a one-time setup, but if you want to load your own world you may need to do some extra things after a server is started/running.
- create a DigitalOcean account and link a credit card. you'll need a credit card to unlock bigger/better server sizes
  - recommended: put a billing alert on your Digital Ocean account just in case you get hacked and someone uses your API key to make more servers
- you'll need SSH access, so the owner (and any other users who will be able to spin up/down the server) should [set up and register SSH keys with the Digital Ocean account](https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys-2)
- create a droplet (aka the server), likely a 4vCPU / 8 GB RAM / 160GB SSD running Ubuntu
  - Note that you can build larger servers from a backup, but not smaller ones.
  - This guide works with Ubuntu, but if you prefer a different flavor of linux it will probably still work
- log into the droplet using SSH
  - this isn't a high-security application with anything other than your valheim world to protect, so we'll just do everything as root.
- [install docker](https://docs.docker.com/engine/install/) in the droplet
  - don't blindly copy-paste from the instructions, they require some choices; you want to use the stable release
- [install docker-compose](https://docs.docker.com/compose/install/) in the droplet
- [follow this guide](https://www.digitalocean.com/community/tutorials/how-to-setup-additional-entropy-for-cloud-servers-using-haveged) to prevent `docker-compose` from [hanging while executed via ssh](https://github.com/docker/compose/issues/6678#issuecomment-526831488)
- clone this repository into the server
- copy `docker-compose.yml.template` into `docker-compose.yml` and adjust it as necessary to customize your server
- `docker-compose up -d` to start it up
- `docker-compose logs --tail=100 -f` to monitor
- if you're going to load your own world or anything, this would be the time to do it
  - you can get into the docker container where the server is actually running with `docker exec -it valheim bash`
- power off the server
- make a snapshot of it named the same as `<name from config>`

### once a server is configured, you can interact with cloud instances of it using the client tool
- make sure you've completed the pre-requisites once:
  - [create an ssh key](https://docs.github.com/en/github/authenticating-to-github/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) and send the `.pub` one to the owner of the DigitalOcean admin account (likely found in `~/.ssh` directory)
  - update the `client/config.yaml` file with an API key, provided by the owner of a DigitalOcean admin account

The client part of this codebase will use a DigitalOcean API key along with a digital ocean python API to instrument the server.  Save money by only starting the server when you'll use it, and stop it when you're not!
- first time only, open a terminal and:
  - `apt-get install python3-venv`
  - `python3 -m venv valheim_venv`
- every time you open a new terminal, activate the virtualenv: `source valheim_venv/bin/activate`
  - you'll see your terminal prefixed with `(valheim_venv) `
- `git pull` the latest on the `main` branch
- if `git pull` grabbed any updates, do this: `pip install -r requirements.txt`
  - installs any new libraries introduced by new code

#### valhalla.py
a command line tool to interact with cloud servers ("droplets") and valheim servers running on them. 
execute it as:
- make sure you activated the virtualenv
- execute: `cd client`
- execute: `python valhalla.py`

At any time, enter `help` to see the commands available to you

#### from zero to valhallha
When you want to play:
- make sure you activated the virtualenv
- execute: `cd client`
- execute: `python valhalla.py`
- valhalla command: `full_up`
  - to fire it up from scratch, `full_up` performs the following
    - DigitalOcean API: identify the most recent snapshot
    - DigitalOcean API: create a droplet from a snapshot
    - ssh command to droplet to start docker container(s)
    - ssh command to droplet to start & update valheim server inside docker containers
    - display the IP of the server to the user

#### spin down server
When you're done, `full_down` will do the following (use `help` to fix any issues):
- make sure you activated the virtualenv
- execute: `cd client`
- execute: `python valhalla.py`
- valhalla command: `full_down`
- DigitalOcean API: identify a running droplet
  - ssh command to droplet to stop valheim server
  - DigitalOcean API: power down droplet (so we can snapshot it safely, this doesn't save money)
  - DigitalOcean API: snapshot droplet
  - DigitalOcean API: if there are more than the configured number-snaps-to-keep, delete oldest snapshots as necessary
  - DigitalOcean API: destroy droplet (this actually saves money)

Note that this process may take 20+ minutes, and sometimes is interrupted. You can check
to see if anything is running by the command `droplet_show`, and see if a droplet backup completed
using `snapshot_list`.  Use `help` to figure out what you can do to fix it.

#### to update server
In theory, the server should update as part of this repo's start-server command... but it often fails.
- `ssh root@<droplet IP address>`
- `cd ~/valheim-digitalocean/server`
- `docker-compose start valheim`
- `docker exec -it valheim bash`
- `cd /home/steam/valheim`
- `odin stop`
- `odin update`
