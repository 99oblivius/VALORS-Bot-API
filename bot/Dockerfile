FROM python:3.12

ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod -R 655 /install.sh && /install.sh && rm /install.sh

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /bot

RUN pip install uv
COPY VALORS-Match-Making-Bot/requirements.txt requirements.txt
RUN uv pip install --system --no-cache -r requirements.txt

COPY VALORS-Match-Making-Bot/ .

CMD ["python", "./src/main.py"]
RUN python -m nextcord -v
