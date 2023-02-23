FROM alpine
RUN apk update && apk add gpg
ENTRYPOINT [ "gpg" ]
