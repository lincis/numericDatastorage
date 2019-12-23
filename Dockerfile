FROM python:latest
RUN uname -a
RUN apt-get update
RUN apt-get -y --no-install-recommends install libpq-dev
RUN apt-get -y --no-install-recommends install redis-server systemd
RUN systemctl enable redis-server
COPY . /app
RUN pip install -r /app/requirements.txt
