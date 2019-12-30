FROM python:3.6
RUN uname -a
RUN apt-get update && apt-get install -y libpq-dev redis-server \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
COPY . /app
RUN pip install -r /app/requirements.txt
