FROM python:3.8-alpine
MAINTAINER Carlos Nunez <dev@carlosnunez.me>
ENV PYTHONPATH="${PYTHONPATH};/vendor"

RUN apk update
RUN apk add gcc libffi-dev musl-dev

COPY ./vendor /vendor

RUN mkdir /app
COPY . /app
WORKDIR /app

USER nobody
