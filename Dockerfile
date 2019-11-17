FROM tiangolo/uwsgi-nginx-flask
RUN uname -a
RUN apt-get install libpq-dev
COPY . /app
RUN pip install -r requirements.txt
