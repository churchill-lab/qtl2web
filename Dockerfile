FROM python:3.10-bookworm

LABEL maintainer="Matt Vincent <matt.vincent@jax.org>"

# install what we need
RUN apt-get update; \
	apt-get install -y --no-install-recommends \
        build-essential \
        libpcre3 \
        libpcre3-dev \
		nginx \
		supervisor \
	; \
	rm -rf /var/lib/apt/lists/*

ENV INSTALL_PATH /app
RUN mkdir -p $INSTALL_PATH/cache && \
    chmod a+w $INSTALL_PATH/cache
WORKDIR $INSTALL_PATH

RUN useradd --no-create-home nginx
RUN rm /etc/nginx/sites-enabled/default


# Copy the Nginx global conf
COPY ./conf/nginx.conf /etc/nginx/
COPY ./conf/mime.types /etc/nginx/mime.types

# Copy the Flask Nginx site conf
COPY ./conf/flask-site-nginx.conf /etc/nginx/conf.d/

# Copy the base uWSGI ini file to enable default dynamic uwsgi process number
COPY ./conf/uwsgi.ini /etc/uwsgi/

# Custom Supervisord config
COPY ./conf/supervisord.conf /etc/supervisord.conf

# Copy the OpenSSL config
COPY ./conf/openssl.conf /etc/openssl.conf
ENV OPENSSL_CONF /etc/openssl.conf

# copy python requirements file
COPY requirements.txt /tmp/requirements.txt

# Uncomment the following when wanting to force re-compile of anything below
#ADD "https://www.random.org/cgi-bin/randbyte?nbytes=10&format=h" skipcache

# install the requirements
RUN pip install -r /tmp/requirements.txt && \
    pip install uwsgi && \
    rm -r /root/.cache

# Add app
COPY ./qtl2web /app/qtl2web
COPY ./qtl2web/static /app/static

CMD ["/usr/bin/supervisord"]

