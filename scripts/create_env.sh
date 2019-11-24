#!/usr/bin/env bash

test -f ".env.example" || { echo "Please create .env.example" && exit 1; }
sed '/^#/d; /^$/d; s/="change me"/=/' .env.example > .env
