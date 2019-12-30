FROM python:3.6
RUN uname -a
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev=11.5-1+deb10u1 redis-server=5:5.0.3-4+deb10u1 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
COPY . /app
RUN pip install -r /app/requirements.txt
