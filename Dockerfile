FROM alpine:3.9.3

LABEL maintainer="Matt Vincent <matt.vincent@jax.org>" \
	  version="1.1.0"

# install what we need
RUN apk add --no-cache \
    python3 \
    bash \
    nginx \
    uwsgi \
    uwsgi-python3 \
    supervisor && \
    rm /etc/nginx/conf.d/default.conf

ENV INSTALL_PATH /app
RUN mkdir -p $INSTALL_PATH/cache && \
    chmod a+w $INSTALL_PATH/cache
WORKDIR $INSTALL_PATH

# Copy the Nginx global conf
COPY ./conf/nginx.conf /etc/nginx/

COPY ./conf/mime.types /etc/nginx/mime.types

# Copy the Flask Nginx site conf
COPY ./conf/flask-site-nginx.conf /etc/nginx/conf.d/

# Copy the base uWSGI ini file to enable default dynamic uwsgi process number
COPY ./conf/uwsgi.ini /etc/uwsgi/

# Custom Supervisord config
COPY ./conf/supervisord.conf /etc/supervisord.conf

# copy python requirements file
COPY requirements.txt /tmp/requirements.txt

# install the requirements
RUN python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    pip3 install -r /tmp/requirements.txt && \
    rm -r /root/.cache

# Add app
COPY ./qtl2web /app/qtl2web
COPY ./qtl2web/static /app/static

RUN /bin/sh -c cat /app/qtl2web/entrust_l1k.cer >> /usr/lib/python3.6/site-packages/certifi/cacert.pem

CMD ["/usr/bin/supervisord"]

