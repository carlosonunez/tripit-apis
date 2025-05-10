#!/usr/bin/env bash
source $(dirname "$0")/helpers/shared_secrets.sh
TERRAFORM_STATE_S3_KEY="${TERRAFORM_STATE_S3_KEY?Please provide a S3 key to store TF state in.}"
TERRAFORM_STATE_S3_BUCKET="${TERRAFORM_STATE_S3_BUCKET?Please provide a S3 bucket to store state in.}"
AWS_REGION="${AWS_REGION?Please provide an AWS region.}"
ENVIRONMENT="${ENVIRONMENT:-test}"

set -eo pipefail
action=$1
shift

mkdir /config
if test "$IS_LOCAL" == true
then
  >&2 echo "INFO: Setting local provider config"
  cp /app/provider-local.tf /config
  export AWS_ENDPOINT_URL="http://localstack:4566"
else
  cp /app/provider.tf /config
fi
cp /app/infra.tf /config

cd /config
tofu init --backend-config="bucket=${TERRAFORM_STATE_S3_BUCKET}" \
  --backend-config="key=${TERRAFORM_STATE_S3_KEY}/${ENVIRONMENT}" \
  --backend-config="region=$AWS_REGION" && \

tofu $action $*
