FROM python:3.9-slim

WORKDIR /app

VOLUME /hostpipe

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY src/ .

CMD ["python", "server.py"]
