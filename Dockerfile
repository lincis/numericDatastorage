FROM tiangolo/uwsgi-nginx-flask:python3.7
RUN uname -a
RUN apt-get update
RUN apt-get -y --no-install-recommends install libpq-dev
RUN apt-get -y --no-install-recommends install redis-server
RUN update-rc.d -f redis-server enable
RUN update-rc.d redis-server enable
COPY . /app
RUN sed -i 's/app/socketio/g' /app/uwsgi.ini
RUN pip install -r requirements.txt
