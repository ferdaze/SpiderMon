#!/bin/bash

# Ensure log file exists
touch /var/log/spidermon-sender.log

# Start cron
cron -f
