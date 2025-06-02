# Spider-Mon
Spider is a network monitoring tool that has beacons that have senders and recievers that use RTP to monitor network health in a full mesh. It can be scaled to get a more cleaner picture of nextwork health.

## Install
### Required Libraries:
```
pip install prometheus_client numpy
```

### 1.Ensure sender.py and receiver.py are executable
Save sender.py and receiver.py somewhere permanent, for example:
```
sudo mkdir -p /opt/spider-mon/
sudo cp sender.py /opt/spider-mon/
sudo chmod +x /opt/spider-mon/sender.py
sudo cp receiver.py /opt/spider-mon/
sudo chmod +x /opt/spider-mon/receiver.py
```

### 2. Test manually before continuing
Make sure Python, Prometheus client, and numpy are available:
```
python3 /opt/spider-mon/sender.py
python3 /opt/spider-mon/receiver.py
```
If you're using a virtual environment:
* Update the path to python3 accordingly, e.g. /opt/rtp_test/venv/bin/python.

### 3. Create Systemd Service Unit File
Create a new file called:
```
sudo nano /etc/systemd/system/spider-mon-receiver.service
```
Paste the following contents:
```
[Unit]
Description=spider-mon Receiver Beacon Agent
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/spider-mon/receiver.py
WorkingDirectory=/opt/spider-mon
Restart=always
RestartSec=5

StandardOutput=append:/var/log/spider-mon-receiver.log
StandardError=append:/var/log/spider-mon-receiver.log

# Optional: give it a low priority
Nice=10

[Install]
WantedBy=multi-user.target
```
Notes:
* Update python3 to the full path if needed (e.g. /opt/rtp_test/venv/bin/python).
* Append mode keeps logs instead of overwriting.
* sudo is required for /var/log writing.

### 4. Give Python Script Permission to Write Log
Set up /var/log/spider-mon-sender.log and /var/log/spider-mon-receiver.log:
```
sudo touch /var/log/spider-mon-sender.log
sudo chown root:root /var/log/spider-mon-sender.log
sudo chmod 644 /var/log/spider-mon-sender.log
sudo touch /var/log/spider-mon-receiver.log
sudo chown root:root /var/log/spider-mon-receiver.log
sudo chmod 644 /var/log/spider-mon-receiver.log
```
Ensure your script doesn't attempt to open/modify the log itself — systemd handles that.

### 5. Enable and Start the Service
```
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

sudo systemctl enable spider-mon-receiver.service
sudo systemctl start spider-mon-receiver.service
```
Check status:
```
sudo systemctl status spider-mon-receiver.service
```

### 5 Add sender.py to crontab
```
* * * * * /home/user/rtp-env/bin/python3 /opt/spider-mon/sender.py >> /var/log/spider-mon-sender.log 2>&1
```
