import socket
import time
import random
import struct
import threading
import os
import json
import requests
from datetime import datetime, timedelta, timezone

# Configuration
DESTINATIONS_URL = "https://raw.githubusercontent.com/ferdaze/Spider-Mon/refs/heads/main/destinations.json"
CACHE_FILE = "cached_destinations.json"
CACHE_TTL = 86400  # 1 day
INTERVAL = 0.02  # 20 ms
DURATION = 45  # seconds
RATE = 8000  # RTP timestamp rate for audio
PAYLOAD_TYPE = 0
SSRC = 12345
START_DELAY_SECONDS = 61  # Start 1 second after receiver

def get_own_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"

def is_cache_valid(filepath, ttl):
    if not os.path.exists(filepath):
        return False
    age = time.time() - os.path.getmtime(filepath)
    return age < ttl

def fetch_destinations():
    if is_cache_valid(CACHE_FILE, CACHE_TTL):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            print("[SENDER] Cached file is invalid. Removing...")
            os.remove(CACHE_FILE)

    try:
        print(f"[SENDER] Fetching destinations from {DESTINATIONS_URL}")
        response = requests.get(DESTINATIONS_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return data
    except Exception as e:
        print(f"[SENDER] Failed to fetch destinations: {e}")
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        raise RuntimeError("Cannot load destinations.")

def wait_until(target_time):
    now = datetime.now(timezone.utc)
    delay = (target_time - now).total_seconds()
    if delay > 0:
        print(f"[SENDER] Sleeping for {delay:.2f} seconds...")
        time.sleep(delay)

def create_rtp_packet(seq, timestamp):
    version = 2
    header = (version << 14) | PAYLOAD_TYPE
    rtp_header = struct.pack("!HHL", header, seq, timestamp)
    ssrc = struct.pack("!L", SSRC)
    payload = bytes([random.randint(0, 255)] * 160)
    return rtp_header + ssrc + payload

def send_stream(sock, target):
    ip, port = target["ip"], target["port"]
    name = target.get("name", f"{ip}:{port}")
    print(f"[SENDER] Sending to {name} ({ip}:{port})")
    seq = 0
    timestamp = 0
    start_time = time.time()
    while time.time() - start_time < DURATION:
        pkt = create_rtp_packet(seq, timestamp)
        sock.sendto(pkt, (ip, port))
        seq = (seq + 1) % 65536
        timestamp += int(RATE * INTERVAL)
        time.sleep(INTERVAL)
    print(f"[SENDER] Finished sending to {name}")

def main():
    print("[SENDER] Starting sender.py")
    start_time = datetime.now(timezone.utc).replace(second=0, microsecond=0) + timedelta(seconds=START_DELAY_SECONDS)
    print(f"[SENDER] Scheduled start time: {start_time.isoformat()}")

    own_ip = get_own_ip()
    print(f"[SENDER] Detected own IP: {own_ip}")

    destinations = fetch_destinations()
    targets = [d for d in destinations if d["ip"] != own_ip]

    if not targets:
        print("[SENDER] No valid destinations after filtering self.")
        return

    wait_until(start_time)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    threads = []
    for t in targets:
        thread = threading.Thread(target=send_stream, args=(sock, t))
        thread.start()
        threads.append(thread)

    for t in threads:
        t.join()
    sock.close()

if __name__ == "__main__":
    main()
