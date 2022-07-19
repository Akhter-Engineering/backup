FROM postgres:14.4-alpine3.16

ENV ROOT /main

WORKDIR $ROOT

RUN apk update \
    && apk add gzip \
    && apk add --no-cache python3 \
    && if [ ! -e /usr/bin/python ]; then ln -sf python3 /usr/bin/python ; fi \
    && python -m ensurepip \
    && rm -r /usr/lib/python*/ensurepip \
    && pip3 install --no-cache --upgrade pip setuptools wheel \
    && if [ ! -e /usr/bin/pip ]; then ln -s pip /usr/bin/pip ; fi

RUN pip install boto
RUN pip install slackclient

# Add files
COPY src/* $ROOT/

# Add start script
RUN chmod +x $ROOT/start.sh

ENV PATH="$ROOT:$PATH"
