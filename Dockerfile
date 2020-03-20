FROM python:3.8-alpine as base
MAINTAINER Carlos Nunez <dev@carlosnunez.me>

COPY requirements.txt .
RUN pip install -r requirements.txt

FROM base as app
ENV FLASK_APP=tripit-api
RUN mkdir /app
COPY . /app
WORKDIR /app
USER nobody
