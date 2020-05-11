#!/usr/bin/env bash
source $(dirname "$0")/helpers/shared_secrets.sh
set -e

get_api_gateway_endpoint() {
  >&2 echo "INFO: Getting integration test API Gateway endpoint."
  endpoint_url=$(docker-compose -f docker-compose.deploy.yml run \
      --rm serverless info --stage develop | \
    grep -E 'http.*\/ping' | \
    sed 's/.*\(http.*\)\/ping/\1/' | \
    tr -d $'\r' | \
    tr -d $'\n')

  >&2 echo "INFO: Getting API Gateway default API key."
  api_key=$(docker-compose -f docker-compose.deploy.yml \
      run --rm serverless info --stage develop | \
    grep -E 'default-tripit-key-dev:' | \
    sed 's/.*default-tripit-key-dev: //' | \
    tr -d $'\r' | \
    tr -d $'\n'
  )
  if test -z "$endpoint_url"
  then
    >&2 echo "ERROR: We couldn't find a deployed endpoint."
    exit 1
  fi
  if test -z "$api_key"
  then
    >&2 echo "ERROR: We couldn't find an API key."
    exit 1
  fi
  export API_GATEWAY_URL="$endpoint_url"
  export API_KEY="$api_key"
  write_secret "$endpoint_url" "endpoint_name"
  write_secret "$api_key" "api_key"
}

get_infrastructure_secrets() {
  >&2 echo "INFO: Getting infrastructure secrets."
  for output_var in app_account_ak app_account_sk certificate_arn
  do
    secret_value="$(docker-compose -f docker-compose.deploy.yml run --rm terraform output "$output_var" | \
      tail -1 | \
      tr -d $'\r' | \
      tr -d $'\n')"
    write_secret "$secret_value" "$output_var"
  done
}

remove_secret_folder_if_present &&
  get_api_gateway_endpoint &&
  get_infrastructure_secrets
