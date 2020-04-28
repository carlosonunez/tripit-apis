FROM python:3.8-alpine as base
MAINTAINER Carlos Nunez <dev@carlosnunez.me>
ARG IS_FOR_VENDORING_SERVICE

COPY vendor /vendored
COPY requirements.txt /
RUN if [ "$IS_FOR_VENDORING_SERVICE" != "true" ]; \
    then \
      pip install -r /requirements.txt --no-index --find-links file:///vendored; \
    fi

FROM base as app
ENV FLASK_APP=tripit-api
ENV PYTHONPATH="${PYTHONPATH};/vendor"
RUN mkdir /app
COPY . /app
WORKDIR /app
USER nobody
