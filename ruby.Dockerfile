FROM ruby:2.5-alpine
MAINTAINER Carlos Nunez <dev@carlosnunez.me>
ARG ENVIRONMENT

RUN apk add --no-cache ruby-dev  ruby-nokogiri build-base libxml2-dev \
libxslt-dev postgresql-dev sqlite sqlite-libs sqlite-dev less

COPY Gemfile /
RUN bundle install --gemfile /Gemfile

WORKDIR /app
ENTRYPOINT ["ruby", "-e", "puts 'Welcome to tripit-api'"]
