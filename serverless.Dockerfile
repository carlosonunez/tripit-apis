FROM node:alpine
MAINTAINER Carlos Nunez <dev@carlosnunez.me>

RUN npm install -g serverless@3.38.0 --progress=false --no-audit
RUN npm install -g serverless-domain-manager@6.3.1 --save-dev --progress=false --no-audit
