FROM tiangolo/uwsgi-nginx-flask:python3.7
RUN uname -a
RUN apt-get -y --no-install-recommends install libpq-dev
RUN apt-det -y --no-install-recommends install redis-server
RUN systemctl enable redis-server
COPY . /app
RUN pip install -r requirements.txt
