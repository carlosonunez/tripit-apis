#!/usr/bin/env bash
print_aws_cred_env_vars() {
  aws_token_data=$(tail -1 /secrets/aws_token)
  ak="$(awk '{print $2}' <<< "$aws_token_data")"
  sk="$(awk '{print $4}' <<< "$aws_token_data")"
  st="$(awk '{print $5}' <<< "$aws_token_data")"
  cat <<-EOF
export AWS_ACCESS_KEY_ID=$ak
export AWS_SECRET_ACCESS_KEY=$sk
export AWS_SESSION_TOKEN=$st
EOF
}

AWS_SESSION_NAME="tripit-apis-session-$(date +%s)"
aws_token_data=""
if test -f "/secrets/aws_token" && test -f "/secrets/aws_token_expiration_date"
then
  now=$(date +%s)
  token_expiry=$(cat /secrets/aws_token_expiration_date)
  if test -z "$token_expiry" || test "$now" -lt "$token_expiry"
  then
    print_aws_cred_env_vars
    exit 0
  fi
fi
unset AWS_SESSION_TOKEN
>&2 echo "INFO: Renewing AWS session token; hang on"
aws sts assume-role \
  --role-arn "$AWS_ROLE_ARN" \
  --external-id "$AWS_STS_EXTERNAL_ID" \
  --role-session-name "$AWS_SESSION_NAME" \
  --output text > /secrets/aws_token || exit 1
>&2 echo "INFO: Token renewed; expires in an hour."
date -d '+1 hour' +%s > /secrets/aws_token_expiration_date

print_aws_cred_env_vars
