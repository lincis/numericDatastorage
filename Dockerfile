FROM tiangolo/uwsgi-nginx-flask:python-3.7
RUN uname -a
RUN apt-get -y --no-install-recommends install libpq-dev
COPY . /app
RUN pip install -r requirements.txt
