# valheim-digitalocean

### server setup
The server is mostly a one-time setup, but if you want to load your own world you may need to do some extra things after a server is started/running.
- create a DigitalOcean account and link a credit card
- create a "droplet", likely a 4vCPU / 8 GB RAM / 160GB SSD
- log into the server (ssh is best)
- install docker
- install docker-compose
- clone repo into server
- adjust `docker-compose.yml` as necessary
- `docker-compose up -d` to start it up
- `docker-compose logs --tail=100 -f` to monitor
- power off the server
- make a snapshot of it named the same as `<name from config>`

### client setup
The client part of this codebase will use a DigitalOcean API key along with a digital ocean python API to instrument the server.  The key reasons for having startup/shutdown scripts instead of leaving it running 24/7 are:
- cost
- time in game may pass without any players present?
- mostly cost though

pre-requisites
- update the `config.yaml` file with required information

When you want to play, the `start_server.py` script will do the following (presumes ssh access to the droplet is configured):
- DigitalOcean API: create a "droplet" (DigitalOcean's name for a server instance) from a snapshot
- ssh command to droplet, start docker container(s): `cd ~/valheim-digitalocean/server; docker-compose up -d`
- ssh command to drople, start valheim servert: `cd ~/valheim-digitalocean/server; docker exec -it valheam odin start`
- display the IP of the server to the user
- game on!

#### to start server
- first time only, do this: `python3 -m venv valheim_venv`
- every time, do this: `source valheim_venv/bin/activate`
- first time only, do this: `pip install -r requirements.txt`
- execute: `python client/start_server.py`

When you're done, the `stop_server.py` script will do the following
- DigitalOcean API: identify a running droplet
- ssh command to droplet; stop valheim server: `cd ~/valheim-digitalocean/server; docker exec -it valheam odin stop`
- DigitalOcean API: power down droplet (so we can snapshot it safely)
- DigitalOcean API: snapshot droplet to `<name from config>_new`
- DigitalOcean API: delete old snapshot named `<name from config>`
- DigitalOcean API: rename new snapshot `<name from config>_new` to `<name from config>`
- DigitalOcean API: destroy droplet (saves money)


#### to stop server
- every time, do this: `source valheim_venv/bin/activate`
- execute: `python client/stop_server.py`
