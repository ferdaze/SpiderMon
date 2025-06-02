import socket
import struct
import time
import numpy as np
from datetime import datetime, timedelta, timezone
from prometheus_client import start_http_server, Gauge

# Configuration
PORT = 5004
DURATION = 30
INTERVAL = 0.02
START_DELAY_SECONDS = 60  # Start on the next full minute

# Prometheus Metrics
packet_loss_metric = Gauge("rtp_packet_loss_percent", "RTP Packet Loss (%)", ['source_ip'])
jitter_metric = Gauge("rtp_jitter_ms", "RTP Jitter (ms)", ['source_ip'])
mos_metric = Gauge("rtp_mos_score", "Mean Opinion Score", ['source_ip'])

def wait_until(target_time):
    now = datetime.now(timezone.utc)
    delay = (target_time - now).total_seconds()
    if delay > 0:
        print(f"[RECEIVER] Waiting {delay:.2f} seconds for synchronized start...")
        time.sleep(delay)

def calculate_mos(packet_loss, jitter):
    r = 93.2 - packet_loss * 2.5 - jitter * 0.1
    r = max(0, min(r, 100))
    mos = 1 + 0.035 * r + (r * (r - 60) * (100 - r) * 7e-6)
    return max(min(mos, 4.5), 1.0)

def main():
    print("[RECEIVER] Starting receiver.py")
    start_time = datetime.now(timezone.utc).replace(second=0, microsecond=0) + timedelta(seconds=START_DELAY_SECONDS)
    print(f"[RECEIVER] Scheduled start time: {start_time.isoformat()}")
    wait_until(start_time)

    # Start Prometheus exporter
    start_http_server(8000)

    print(f"[RECEIVER] Listening on UDP port {PORT}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', PORT))
    sock.settimeout(DURATION + 5)

    buffers = {}
    test_start = time.time()

    while time.time() - test_start < DURATION:
        try:
            data, addr = sock.recvfrom(2048)
            now = time.time()
            ip = addr[0]
            if len(data) < 12:
                continue

            if ip not in buffers:
                buffers[ip] = {
                    'expected_seq': None,
                    'received': 0,
                    'lost': 0,
                    'last_arrival': None,
                    'jitter_list': [],
                }

            buffer = buffers[ip]
            seq = struct.unpack('!HHL', data[:8])[1]

            if buffer['expected_seq'] is None:
                buffer['expected_seq'] = (seq + 1) % 65536
            else:
                expected = buffer['expected_seq']
                if seq != expected:
                    buffer['lost'] += (seq - expected) % 65536
                buffer['expected_seq'] = (seq + 1) % 65536

            if buffer['last_arrival'] is not None:
                transit = now - buffer['last_arrival']
                jitter = abs(transit - INTERVAL) * 1000
                buffer['jitter_list'].append(jitter)

            buffer['last_arrival'] = now
            buffer['received'] += 1

        except socket.timeout:
            break

    # Process results
    for ip, b in buffers.items():
        total = b['received'] + b['lost']
        loss_pct = 100.0 * b['lost'] / total if total else 0.0
        jitter_avg = float(np.mean(b['jitter_list'])) if b['jitter_list'] else 0.0
        mos = calculate_mos(loss_pct, jitter_avg)

        packet_loss_metric.labels(source_ip=ip).set(loss_pct)
        jitter_metric.labels(source_ip=ip).set(jitter_avg)
        mos_metric.labels(source_ip=ip).set(mos)

        print(f"[RECEIVER] From {ip} - Loss: {loss_pct:.2f}%, Jitter: {jitter_avg:.2f} ms, MOS: {mos:.2f}")

    sock.close()

if __name__ == "__main__":
    main()
