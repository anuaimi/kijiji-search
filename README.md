# Kijiji Search

## Overview

This will run a search against Kijiji's websetup regularly and notify you by email if there are any new listings.  This is useful of items that are hard to find and that don't last long. It does this by using pyppeteer (which uses a real browser) and doing the search the same way that a user would.

You need to generate the query yourself in a real browser and copy the results to `data/queries.json`.  The file can have multiple queries in it and all of them will be run each cycle.

## Setup

make sure you have Pipenv install and then create a new environment for the project

```bash
pip install pipenv
pipenv install
pipenv shell
# pipenv --venv
# add above to python.pythonPath in .vscode/settings.json
```

To be able to send email, the code needs a MailJet api key and secret. You can set them as environment variables or add them to the config file (see `config-sample.json`)

```bash
export MJ_API_KEY="--api-key--"
export MJ_API_SECRET="--api-secret--"
```

## Build

```bash
docker build -t anuaimi/kijiji-search .
```

If you want to deploy the container to the cloud, you need to push the image to a registry

```bash
docker push anuaimi/kijiji-search
```

## Deploying

The simplest way to run this code is to get a small VM at public cloud provider and run it there.  The example below uses DigitalOcean.  They have VMs that have Docker pre-installed.  Note, replace `--fingerprint--` with your actual SSH key fingerprint.

```bash
doctl compute droplet create --image docker-20-04 --size s-1vcpu-1gb --region tor1 --ssh-keys --fingerprint-- kijiji-search
ssh root@serverIP
```

## Running

You need to define the kijiji search and put the details in the `data/queries.json` file.

with secrets

```bash
export MY_API_KEY=""
export MY_API_SECRET=""
docker run -it --name kijiji-search -e MJ_API_KEY=$MJ_API_KEY -e MJ_API_SECRET=$MJ_API_SECRET -v $PWD/data:/data anuaimi/kijiji-search
```

You can find a pre-built docker container at 
https://hub.docker.com/repository/docker/anuaimi/kijiji-search

## Debugging

You can debug docker issues by starting a python container and running the various command in the docker file.  Also you can use the following to debug pyppeteer issues

```python
from pyppeteer.launcher import Launcher
' '.join(Launcher().cmd)
```
