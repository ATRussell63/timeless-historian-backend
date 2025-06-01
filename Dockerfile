FROM python:3.13-alpine
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY test ./test
COPY convert.lua .
COPY dkjson.lua .
COPY poll.py .
COPY poll.sh .
COPY db_init_script.pgsql .
COPY run.py .
COPY config ./config

EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "-w", "2", "run:app"]
