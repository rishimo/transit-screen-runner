#!/bin/bash
# this script will be run on reboot by crontab

# cd into git repo
cd /home/admin/transit-screen-runner

# pull repo to update and update submodules
git pull --recurse-submodules

# activate venv containing necessary modules
source /home/admin/venv/bin/activate

# run screen program
python weather.py