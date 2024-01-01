#!/bin/sh

date
kill $(pgrep python)
echo "killed running python instance"

/home/admin/venv/bin/python /home/admin/transit-screen-runner/weather.py
echo "started script"