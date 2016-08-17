FROM ubuntu:14.04

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        git \
	nano \
        wget \
        python-dev \
        python-pip \
	curl && \
    rm -rf /var/lib/apt/lists/*

RUN apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main" > /etc/apt/sources.list.d/pgdg.list
RUN apt-get update && apt-get install -y python-software-properties software-properties-common postgresql-9.3 postgresql-client-9.3 postgresql-contrib-9.3 libpq-dev


# Nodejs 4.4.4
RUN curl -sL https://deb.nodesource.com/setup_4.x | sudo -E bash -
RUN apt-get install -y nodejs


# pip Pillow dependencies
RUN apt-get build-dep -y python-imaging
RUN apt-get install -y \
	libjpeg62 libjpeg62-dev

WORKDIR /home/app/

# preinstall most pip dependancies to save time
RUN pip install \
	"Flask==0.10.1" \
	"Flask-Login==0.2.6" \
	"itsdangerous==0.24" \
	"Jinja2==2.8" \
	"MarkupSafe==0.23" \
	"psycopg2==2.6.1" \
	"SQLAlchemy==1.0.1" \
	"Werkzeug==0.11.9" \
	"Bokeh==0.12.1" \
	"sqlalchemy-utils==0.32.9" \
	"Pillow==3.1.0"
# node module is hardcoded here (will always be the same)
RUN npm install express@4.13.4 http-proxy@1.14.0
# now install actual dependancies (should be done already)
COPY application/requirements.txt ./application/requirements.txt
RUN pip install -r ./application/requirements.txt

# copy app from host
COPY . ./


#RUN psql -h $DB_PORT_5432_TCP_ADDR -p $DB_PORT_5432_TCP_PORT -U postgres $DB_ENV_POSTGRES_PASSWORD -c \l
ENV APP_HOSTNAME "0.0.0.0"
ENV FLASK_RELOAD_DISABLE "True"
ENV FLASK_DEBUG_DISABLE "True"
RUN echo "print 'SQLALCHEMY_URL', SQLALCHEMY_DATABASE_URI" >> config.py
EXPOSE 80
CMD node load-balancer.js > application/images/log.txt
