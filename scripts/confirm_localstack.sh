#!/usr/bin/env sh
test "$IS_LOCAL" != 'true' && exit 0

nc -z localstack 4566
