#!/usr/bin/env bash
source $(dirname "$0")/helpers/logging.sh

remove_secret() {
  secret_name="${1?Please provide a secret.}"
  rm -f "./secrets/${secret_name}"
}

create_secret_folder_if_not_present() {
  mkdir -p "./secrets/"
}

write_secret() {
  create_secret_folder_if_not_present
  secret="${1?Please provide a secret to write.}"
  secret_filename="$2"
  if test -z "$secret_filename"
  then
    secret_filename=$(echo "$secret" | \
      tr '[:upper:]' '[:lower:]' | \
      tr ' ' '_'
    )
    if test -z "$secret_filename"
    then
      error "Something went wrong while creating a secret, \
as no data was received."
      exit 1
    fi
  fi
  secret_filepath="./secrets/$secret_filename"
  printf "$secret" > "$secret_filepath"
}

remove_secret_folder_if_present() {
  test -d "./secrets" && rm -r ./secrets || true
}
