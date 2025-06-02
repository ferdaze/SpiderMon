import socket
import time
import random
import struct
import threading
from datetime import datetime, timedelta, timezone

# List of destinations
DESTINATIONS = [
    {'name': 'SLKCUTXD', 'ip': '10.24.34.250', 'port': 5004},
    {'name': 'TOR', 'ip': '10.28.34.250', 'port': 5004},

]

INTERVAL = 0.02  # 20ms
DURATION = 45    # seconds
RATE = 8000      # 8 kHz RTP clock rate
PAYLOAD_TYPE = 0
SSRC = 12345

def wait_until_next_minute():
    now = datetime.now(timezone.utc)
    next_minute = (now + timedelta(minutes=1)).replace(second=2, microsecond=0)
    wait = (next_minute - now).total_seconds()
    print(f"[SENDER] Waiting {wait:.2f} seconds until next synchronized start...")
    time.sleep(wait)

def create_rtp_packet(seq, timestamp):
    version = 2
    padding = 0
    extension = 0
    cc = 0
    marker = 0
    header = (version << 14) | (padding << 13) | (extension << 12) | \
             (cc << 8) | (marker << 7) | PAYLOAD_TYPE
    header_data = struct.pack("!HHL", header, seq, timestamp)
    ssrc_data = struct.pack("!L", SSRC)
    payload = bytes([random.randint(0, 255)] * 160)  # 160 bytes = 20ms of PCMU @ 8kHz
    return header_data + ssrc_data + payload

def send_to_target(sock, target):
    ip, port = target['ip'], target['port']
    name = target['name']
    seq = 0
    timestamp = 0
    start = time.time()
    print(f"[SENDER] Sending RTP to {name} at {ip}:{port}")
    while time.time() - start < DURATION:
        pkt = create_rtp_packet(seq, timestamp)
        sock.sendto(pkt, (ip, port))
        seq = (seq + 1) % 65536
        timestamp += int(INTERVAL * RATE)
        time.sleep(INTERVAL)
    print(f"[SENDER] Completed stream to {name}")

def main():
    wait_until_next_minute()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    threads = []
    for target in DESTINATIONS:
        t = threading.Thread(target=send_to_target, args=(sock, target))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    sock.close()

if __name__ == "__main__":
    main()
