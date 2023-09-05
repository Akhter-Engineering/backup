FROM postgres:15.4-alpine3.18

ENV ROOT /main

WORKDIR $ROOT

RUN apk update \
    && apk add gzip \
    && apk add --no-cache python3 \
    && if [ ! -e /usr/bin/python ]; then ln -sf python3 /usr/bin/python ; fi \
    && python -m ensurepip \
    && rm -r /usr/lib/python*/ensurepip \
    && pip3 install --no-cache --upgrade pip setuptools wheel \
    && if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi

RUN pip install boto3
RUN pip install slackclient
RUN pip install PyYAML
RUN pip install requests


# Add files
COPY src/* $ROOT/

# Add start script
RUN chmod +x $ROOT/start.sh

ENV PATH="$ROOT:$PATH"

CMD ["start.sh"]
