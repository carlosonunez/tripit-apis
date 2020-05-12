set -e

_log() {
  level="$1"
  color="$2"
  message="${@:3}"
  >&2 printf "\e[1;37m[$(date +%s.%N | cut -b1-15)]\e[0m \
\e[${color}[$(echo "$level" | tr '[:lower:]' '[:upper:]')]\e[0m \
- \e[4m${FUNCNAME[2]}\e[0m - $message\n"
}

info() {
  _log "INFO" "1;32m" "${@:1}" # Bold Green
}

warn() {
  _log "WARN" "1;33m" "${@:1}" # Bold Yellow
}

error() {
  _log "ERROR" "41m;1;37m" "${@:1}" # Red Background, Bold White
}
