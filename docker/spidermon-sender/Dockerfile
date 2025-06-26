FROM python:3.12-slim

WORKDIR /app

# Install dependencies and cron
RUN apt-get update && apt-get install -y cron && \
    pip install --no-cache-dir requests && \
    apt-get clean

COPY sender.py .
COPY run-cron.sh .

# Add crontab file
COPY cron.schedule /etc/cron.d/sender-cron

# Give execution rights on the cron job and script
RUN chmod 0644 /etc/cron.d/sender-cron
RUN chmod +x /app/run-cron.sh /app/spidermon-sender.py

# Apply cron job
RUN crontab /etc/cron.d/sender-cron

CMD ["bash", "/app/run-cron.sh"]
