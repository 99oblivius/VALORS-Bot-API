FROM python:3.13-slim-bookworm
WORKDIR /app

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
    build-essential python3-dev \
    libffi-dev libssl-dev \
    curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1
ENV PYTHONOPTIMIZE=2

COPY crossplaybot/requirements.txt requirements.txt
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod +x /install.sh && /install.sh && rm /install.sh
RUN pip install uv && uv pip install --system -r requirements.txt

COPY crossplaybot .

ENTRYPOINT ["python"]
CMD ["./main.py"]
