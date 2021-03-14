#!/usr/bin/env bash

# create VM
export SSH_FIGERPRINT=dd:9e:43:2f:37:cd:93:cf:8f:e2:19:0f:a1:02:3e:cf
doctl compute droplet create --image docker-20-04 --size s-1vcpu-1gb --region tor1 --ssh-keys $SSH_FINGERPRINT kijiji-search

# get public IP of VM
export VM_IP=`doctl compute droplet list | egrep -i kijiji-search | awk '{ print $3}'`

scp ~/.ssh/id_rsa root@$VM_IP:/root/.ssh/id_rsa
scp ~/.ssh/id_rsa.pub root@$VM_IP:/root/.ssh/id_rsa.pub

scp data/config.json root@$VM_IP:/root/code/kijiji-search/data/config.json
scp data/queries.json root@$VM_IP:/root/code/kijiji-search/data/queries.json

