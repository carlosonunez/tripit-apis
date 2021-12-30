# source this file into your Bash or zsh session to make some common
# commands available to you while testing the TripIt API.
alias unit="scripts/unit"
alias integration="scripts/integration"
alias integration_no_destroy="KEEP_INTEGRATION_ENVIRONMENT_UP=true scripts/integration"
alias integration_test="KEEP_INTEGRATION_ENVIRONMENT_UP=true NO_DEPLOY=true scripts/integration"
alias integration_test_redeploy_too="KEEP_INTEGRATION_ENVIRONMENT_UP=true DEPLOY_FUNCTIONS_ONLY=true scripts/integration"
alias integration_destroy="remove_functions && remove_infra"
alias remove_functions="docker-compose -f docker-compose.deploy.yml run --rm serverless remove --stage develop"
alias remove_infra="docker-compose -f docker-compose.deploy.yml run --rm terraform destroy"
alias deploy="scripts/deploy"
alias logs="docker-compose -f docker-compose.deploy.yml run --rm serverless logs --stage develop"
alias logs_prod="docker-compose -f docker-compose.deploy.yml run --rm serverless logs --stage v1"
alias serverless="docker-compose -f docker-compose.deploy.yml run --rm serverless"
