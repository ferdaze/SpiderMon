FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY sender.py .

RUN pip install --no-cache-dir requests

CMD ["python", "sender.py"]
