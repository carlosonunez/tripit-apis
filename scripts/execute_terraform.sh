#!/usr/bin/env sh
source $(dirname "$0")/helpers/shared_secrets.sh
TERRAFORM_STATE_S3_KEY="${TERRAFORM_STATE_S3_KEY?Please provide a S3 key to store TF state in.}"
TERRAFORM_STATE_S3_BUCKET="${TERRAFORM_STATE_S3_BUCKET?Please provide a S3 bucket to store state in.}"
AWS_REGION="${AWS_REGION?Please provide an AWS region.}"
ENVIRONMENT="${ENVIRONMENT:-test}"

set -e
action=$1
shift

terraform init --backend-config="bucket=${TERRAFORM_STATE_S3_BUCKET}" \
  --backend-config="key=${TERRAFORM_STATE_S3_KEY}/${ENVIRONMENT}" \
  --backend-config="region=$AWS_REGION" && \

terraform $action $*
