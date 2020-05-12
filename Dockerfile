FROM python:3.8-alpine
MAINTAINER Carlos Nunez <dev@carlosnunez.me>
ENV PYTHONPATH="${PYTHONPATH};/vendor"

COPY ./vendor /vendor

# There are massive performance problems while running Docker on
# non-Linux systems due to realtime volume sync. I could use Docker Sync
# to resolve that, but it's just easier to rebuild the image every time,
RUN mkdir /app
COPY . /app
WORKDIR /app

USER nobody
