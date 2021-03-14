#!/usr/bin/env bash

# remove older python3 
sudo apt update
sudo apt remove -y python3

# update apt to use python package repo
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa

# install version of python we want
sudo apt install -y python3.9
sudo apt install -y python3-pip

mkdir -p /code
cd /code
git clone git@github.com:anuaimi/kijiji-search.git 
# now ready to follow normal project setup (see README.md)
# assume ssh key installed so 