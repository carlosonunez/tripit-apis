#!/usr/bin/env ruby
$LOAD_PATH.unshift('./lib')
if Dir.exist? './vendor'
  $LOAD_PATH.unshift('./vendor/bundle/ruby/**gems/**/lib')
end

require 'tripit'
require 'json'

# Retrieve tokens for autheticated users.
def get_token(event: {}, context: {})
  TripIt::Auth.get_slack_token(event: event)
end

# Begin the Slack OAuth flow manually.
def begin_authentication(event: {}, context: {})
  TripIt::Auth.begin_authentication_flow(event, client_id: ENV['SLACK_APP_CLIENT_ID'])
end

# Slack needs a callback URI to send its code too. This is that callback.
def handle_callback(event: {}, context: {})
  TripIt::Auth.handle_callback(event)
end

# health check. don't need request here...at least not yet.
def ping(event: {}, context: {})
  TripIt::Health.ping
end
