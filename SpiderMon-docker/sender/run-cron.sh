#!/bin/bash

# Ensure log file exists
touch /var/log/sender.log

# Start cron
cron -f
