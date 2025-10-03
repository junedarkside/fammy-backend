FROM python:3.10-alpine
LABEL maintainer="TravelApp"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt /tmp/requirements.txt
COPY ./scripts /scripts
COPY . /app/
WORKDIR /app
EXPOSE 8000


RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client jpeg-dev zlib-dev libjpeg-turbo-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev  linux-headers &&\
    /py/bin/pip install -r /tmp/requirements.txt && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user && \
    chown -R django-user /py && \
    # chmod -R +x /scripts/run.sh
    chmod -R +x /scripts

ENV PATH="/scripts:/py/bin:$PATH"

USER django-user

CMD ["/scripts/run.sh"]
