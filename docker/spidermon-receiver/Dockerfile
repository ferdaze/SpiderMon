FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY spidermon-receiver.py .

RUN pip install --no-cache-dir \
    prometheus_client \
    numpy

# UDP 5004 for RTP, TCP 8000 for Prometheus exporter
EXPOSE 5004/udp
EXPOSE 8000

CMD ["python", "spidermon-receiver.py"]
