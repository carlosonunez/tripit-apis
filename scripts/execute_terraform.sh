#!/usr/bin/env sh
source $(dirname "$0")/helpers/shared_secrets.sh
GOOGLE_TERRAFORM_SVC_ACCOUNT_CREDS="${GOOGLE_TERRAFORM_SVC_ACCOUNT_CREDS?Please provide your Google Cloud credentials in JSON format.}"
TERRAFORM_STATE_GCS_BUCKET="${TERRAFORM_STATE_GCS_BUCKET?Please provide a GCS bucket to store state in.}"
ENVIRONMENT="${ENVIRONMENT:-test}"

set -e
action=$1
shift

export GOOGLE_CREDENTIALS="${GOOGLE_TERRAFORM_SVC_ACCOUNT_CREDS}"

terraform init --backend-config="bucket=${TERRAFORM_STATE_GCS_BUCKET}" \
  --backend-config="prefix=terraform-state/${ENVIRONMENT}" \

terraform $action $* && \
  if [ "$action" == "apply" ]
  then
    mkdir -p ./secrets
    for output_var in app_account_ak app_account_sk certificate_arn
    do
      write_secret "$(terraform output "$output_var")" "$output_var"
    done
  fi
