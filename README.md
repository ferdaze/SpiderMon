# Spider-Mon
Spider is a network monitoring tool that has beacons that have senders and recievers that use RTP to monitor network health in a full mesh. It can be scaled to get a more cleaner picture of nextwork health.

Grafana output
![](https://github.com/ferdaze/Spider-Mon/blob/main/images/Grafana%20Stats.png)

## Install
### Required Libraries:
```
sudo apt install python3-numpy python3-prometheus-client
```

### 1.Ensure sender.py and receiver.py are executable
Save sender.py and receiver.py somewhere permanent, for example:
```
sudo mkdir -p /opt/spider-mon/
cd /opt/spider-mon/
sudo wget https://raw.githubusercontent.com/ferdaze/Spider-Mon/refs/heads/main/sender.py
sudo chmod +x /opt/spider-mon/sender.py
sudo wget https://raw.githubusercontent.com/ferdaze/Spider-Mon/refs/heads/main/receiver.py
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
sudo vi /etc/systemd/system/spider-mon-receiver.service
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
* Update python3 to the full path if needed (e.g. /usr/bin/python3).
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
* * * * * /usr/bin/python3 /opt/spider-mon/sender.py >> /var/log/spider-mon-sender.log 2>&1
```

### 6 Prometheus Configuration
Add this to your Prometheus config (prometheus.yml):
```
  - job_name: 'rtp_receiver_metrics_pdx'
   scrape_interval: 1m
    static_configs:
      - targets: ['10.25.34.250:8000']
 
  - job_name: 'rtp_receiver_metrics_slc'
   scrape_interval: 1m
    static_configs:
      - targets: ['10.24.34.250:8000']
 
  - job_name: 'rtp_receiver_metrics_tor'
   scrape_interval: 1m
    static_configs:
      - targets: ['10.28.34.250:8000']
```
### 7 Grafana Dashboard
In your Grafana panel (e.g., time series panel):
1. Edit the panel
2. Under the query section, locate the Legend field (just below the Prometheus query)
3. Enter this custom legend format:
```
{{job}} - Source {{source_ip}}
```
This will pull from each time series' labels and create exactly the formatting we confirmed.

Example Prometheus Query
```
rtp_jitter_ms
```
And in the “Legend” box:
```
{{job}} - Source {{source_ip}}
```
Now your graph will show:
* rtp_receiver_metrics_slc - Source 10.25.34.250
* rtp_receiver_metrics_pdx - Source 10.24.34.250
