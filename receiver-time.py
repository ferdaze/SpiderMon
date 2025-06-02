import socket
import struct
import time
import numpy as np
from datetime import datetime, timedelta, timezone
from prometheus_client import start_http_server, Gauge

# Configuration
PORT = 5004
DURATION = 45
INTERVAL = 0.02

# Prometheus metrics
packet_loss_metric = Gauge("rtp_packet_loss_percent", "Packet loss (%)", ['source_ip'])
jitter_metric = Gauge("rtp_jitter_ms", "Jitter (ms)", ['source_ip'])
mos_metric = Gauge("rtp_mos_score", "Estimated MOS score", ['source_ip'])

def wait_until_next_minute():
    now = datetime.now(timezone.utc)
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    wait = (next_minute - now).total_seconds()
    print(f"[RECEIVER] Waiting {wait:.2f} seconds until next synchronized start...")
    time.sleep(wait)

def calculate_mos(packet_loss, jitter):
    r = 93.2 - packet_loss * 2.5 - jitter * 0.1
    r = max(0, min(r, 100))
    mos = 1 + 0.035 * r + (r * (r - 60) * (100 - r) * 7e-6)
    return max(min(mos, 4.5), 1.0)

def receive_rtp():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', PORT))
    sock.settimeout(DURATION + 5)

    print(f"[RECEIVER] Listening on UDP {PORT}...")
    buffers = {}

    start_time = time.time()
    while time.time() - start_time < DURATION:
        try:
            data, addr = sock.recvfrom(2048)
            now = time.time()
            if len(data) < 12:
                continue

            ip = addr[0]
            seq = struct.unpack("!HHL", data[:8])[1]

            if ip not in buffers:
                buffers[ip] = {
                    'expected_seq': seq + 1,
                    'received': 1,
                    'lost': 0,
                    'last_arrival': now,
                    'jitter_list': [],
                    'first': True
                }
                continue

            buf = buffers[ip]
            if seq != buf['expected_seq']:
                lost = (seq - buf['expected_seq']) % 65536
                buf['lost'] += lost
            buf['expected_seq'] = (seq + 1) % 65536
            buf['received'] += 1

            if not buf['first']:
                transit_delay = now - buf['last_arrival']
                jitter = abs(transit_delay - INTERVAL) * 1000
                buf['jitter_list'].append(jitter)
            else:
                buf['first'] = False

            buf['last_arrival'] = now

        except socket.timeout:
            break

    # Process results
    for ip, buf in buffers.items():
        total = buf['received'] + buf['lost']
        loss_pct = 100.0 * buf['lost'] / total if total else 0.0
        jitter_avg = float(np.mean(buf['jitter_list'])) if buf['jitter_list'] else 0.0
        mos = calculate_mos(loss_pct, jitter_avg)

        # Set Prometheus metrics
        packet_loss_metric.labels(source_ip=ip).set(loss_pct)
        jitter_metric.labels(source_ip=ip).set(jitter_avg)
        mos_metric.labels(source_ip=ip).set(mos)

        print(f"[RECEIVER][{ip}] Loss: {loss_pct:.2f}%, Jitter: {jitter_avg:.2f} ms, MOS: {mos:.2f}")

    sock.close()

def main():
    start_http_server(8000)  # Prometheus scrapes here
    while True:
        wait_until_next_minute()
        receive_rtp()
        time.sleep(60 - DURATION)  # gap between tests

if __name__ == "__main__":
    main()
