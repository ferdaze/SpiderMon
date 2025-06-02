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
CACHE_TTL = 86400  # 1 day in seconds
INTERVAL = 0.02  # 20 ms
DURATION = 30  # seconds
RATE = 8000  # Hz, RTP clock rate
PAYLOAD_TYPE = 0
SSRC = 12345

def wait_until_next_minute():
    now = datetime.now(timezone.utc)
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    wait = (next_minute - now).total_seconds()
    print(f"[SENDER] Waiting {wait:.2f} seconds until synchronized start...")
    time.sleep(wait)

def get_own_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Try to determine the primary IP used for outbound connections
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def is_cache_valid(file_path, ttl):
    if not os.path.exists(file_path):
        return False
    file_age = time.time() - os.path.getmtime(file_path)
    return file_age < ttl

def fetch_destinations():
    if is_cache_valid(CACHE_FILE, CACHE_TTL):
        try:
            with open(CACHE_FILE, "r") as f:
                content = f.read()
                data = json.loads(content)
                print("[SENDER] Using cached destinations.")
                return data
        except json.JSONDecodeError as e:
            print("[SENDER] Cached file is corrupted. Will attempt to fetch from GitHub...")
            os.remove(CACHE_FILE)

    try:
        print(f"[SENDER] Fetching destinations from GitHub: {DESTINATIONS_URL}")
        response = requests.get(DESTINATIONS_URL, timeout=5)
        response.raise_for_status()
        data = response.json()  # Validate JSON here
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print("[SENDER] Destinations file updated from GitHub.")
        return data
    except Exception as e:
        print(f"[SENDER] Failed to fetch destinations: {e}")
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    content = f.read()
                    data = json.loads(content)
                    print("[SENDER] Using fallback cached destinations.")
                    return data
            except Exception as err:
                print(f"[SENDER] Fallback cache is also unreadable: {err}")
        raise RuntimeError("No valid destinations available.")

def create_rtp_packet(seq, timestamp):
    version = 2
    padding, extension, cc, marker = 0, 0, 0, 0
    header = (version << 14) | (padding << 13) | (extension << 12) | \
             (cc << 8) | (marker << 7) | PAYLOAD_TYPE
    rtp_header = struct.pack("!HHL", header, seq, timestamp)
    ssrc_bytes = struct.pack("!L", SSRC)
    payload = bytes([random.randint(0, 255)] * 160)
    return rtp_header + ssrc_bytes + payload

def send_to_target(sock, target):
    ip, port = target["ip"], target["port"]
    name = target.get("name", f"{ip}:{port}")
    print(f"[SENDER] Starting stream to {name} ({ip}:{port})")
    seq, timestamp = 0, 0
    start_time = time.time()
    while time.time() - start_time < DURATION:
        packet = create_rtp_packet(seq, timestamp)
        sock.sendto(packet, (ip, port))
        seq = (seq + 1) % 65536
        timestamp += int(RATE * INTERVAL)
        time.sleep(INTERVAL)
    print(f"[SENDER] Finished stream to {name}")

def main():
    own_ip = get_own_ip()
    print(f"[SENDER] Own IP: {own_ip}")

    # Fetch and filter destinations
    destinations = fetch_destinations()
    destinations = [d for d in destinations if d["ip"] != own_ip]

    if not destinations:
        print("[SENDER] No valid destinations (excluding sender's own IP). Exiting.")
        return

    # Wait for synchronized start
    wait_until_next_minute()

    # Send to all targets
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    threads = []
    for target in destinations:
        t = threading.Thread(target=send_to_target, args=(sock, target))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    sock.close()

if __name__ == "__main__":
    main()
