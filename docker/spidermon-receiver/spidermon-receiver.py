import socket
import struct
import time
import numpy as np
from datetime import datetime, timedelta, timezone
from prometheus_client import start_http_server, Gauge

# Prometheus Gauges
packet_loss_metric = Gauge("rtp_packet_loss_percent", "RTP Packet Loss (%)", ['source_ip'])
jitter_metric       = Gauge("rtp_jitter_ms", "RTP Jitter (ms)", ['source_ip'])
mos_metric          = Gauge("rtp_mos_score", "Mean Opinion Score", ['source_ip'])

def wait_until(target_time):
    """Pause execution until the specified UTC target time."""
    now = datetime.now(timezone.utc)
    delay = (target_time - now).total_seconds()
    if delay > 0:
        print(f"[RECEIVER] Waiting {delay:.2f} seconds until next test...")
        time.sleep(delay)

def calculate_mos(packet_loss, jitter):
    """
    Estimate MOS score from packet loss (%) and jitter (ms) using G.107 approximation.
    """
    r = 93.2 - packet_loss * 2.5 - jitter * 0.1
    r = max(0.0, min(r, 100.0))
    mos = 1 + 0.035 * r + (r * (r - 60) * (100 - r) * 7e-6)
    return max(min(mos, 4.5), 1.0)

def receive_rtp_once():
    """
    Run a single 45-second RTP listening session and update Prometheus metrics.
    """
    start_log_ts = datetime.now(timezone.utc).isoformat()
    print(f"[RECEIVER] RTP test started at {start_log_ts}Z")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', PORT))
    sock.settimeout(DURATION + 5)

    buffers = {}
    start_time = time.time()

    while time.time() - start_time < DURATION:
        try:
            data, addr = sock.recvfrom(2048)
            now = time.time()
            if len(data) < 12:
                continue
            ip = addr[0]

            if ip not in buffers:
                buffers[ip] = {
                    'expected_seq': None,
                    'received': 0,
                    'lost': 0,
                    'last_arrival': None,
                    'jitter_list': [],
                }

            buf = buffers[ip]
            seq = struct.unpack('!HHL', data[:8])[1]

            if buf['expected_seq'] is not None:
                expected = buf['expected_seq']
                if seq != expected:
                    buf['lost'] += (seq - expected) % 65536

            buf['expected_seq'] = (seq + 1) % 65536
            if buf['last_arrival'] is not None:
                transit = now - buf['last_arrival']
                jitter_ms = abs(transit - INTERVAL) * 1000
                buf['jitter_list'].append(jitter_ms)

            buf['last_arrival'] = now
            buf['received'] += 1

        except socket.timeout:
            break

    sock.close()

    # Process results and export to Prometheus
    for ip, buf in buffers.items():
        total_packets = buf['received'] + buf['lost']
        loss_pct = 100.0 * buf['lost'] / total_packets if total_packets else 0.0
        jitter_avg = float(np.mean(buf['jitter_list'])) if buf['jitter_list'] else 0.0
        mos_score = calculate_mos(loss_pct, jitter_avg)

        packet_loss_metric.labels(source_ip=ip).set(loss_pct)
        jitter_metric.labels(source_ip=ip).set(jitter_avg)
        mos_metric.labels(source_ip=ip).set(mos_score)

        print(f"[RECEIVER] From {ip} - Loss: {loss_pct:.2f}%, Jitter: {jitter_avg:.2f} ms, MOS: {mos_score:.2f}")

def run_test_loop():
    """
    Starts Prometheus exporter and runs repeated tests every TEST_INTERVAL seconds.
    """
    start_http_server(8000)
    print("[RECEIVER] Prometheus metrics exposed at :8000/metrics")

    while True:
        # align to next full minute
        now = datetime.now(timezone.utc)
        next_run = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        wait_until(next_run)

        receive_rtp_once()

        remaining = TEST_INTERVAL - DURATION
        if remaining > 0:
            print(f"[RECEIVER] Sleeping {remaining:.2f} seconds until next test cycle...")
            time.sleep(remaining)

if __name__ == "__main__":
    print("[RECEIVER] Receiver started and running continuously.")
    run_test_loop()
