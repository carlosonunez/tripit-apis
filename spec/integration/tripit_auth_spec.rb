require 'spec_helper'

describe "TripIt OAuth" do
  before(:all) do
    @final_auth_url = String.new
  end

  context "Step 1" do
    it "Should give me a URL to continue authenticating", :integration do
      uri = "#{$api_gateway_url}/auth?reauthenticate=true"
      response = HTTParty.get(uri, {
        headers: { 'x-api-key': $test_api_key }
      })
      expected_message_re = %r{You will need to authenticate into TripIt first; \
click on or copy/paste this URL to get started: \
https://www.tripit.com/oauth/authorize\?oauth_token=[a-zA-Z0-9]+&\
oauth_callback=#{$api_gateway_url}/callback}
      expect(JSON.parse(response.body)['message']).to match expected_message_re
      expect(response.code.to_i).to eq 200
    end
  end

  # We need to use Capybara here since retrieving the final authentication URL
  # requires user action through a GUI.
  context "Step 2" do
    it "Should save my token with my API key", :integration do
      uri = "#{$api_gateway_url}/auth?workspace=#{ENV['TRIPIT_WORKSPACE_NAME']}&reauthenticate=true"
      response = HTTParty.get(uri, {
        headers: { 'x-api-key': $test_api_key }
      })
      message = JSON.parse(response.body)['message']
      auth_url = message.match('^.*get started: (http.*)$').captures[0]

      visit(auth_url)
      click_link "Sign in"
      fill_in "email_address", with: ENV['TRIPIT_SANDBOX_ACCOUNT_EMAIL']
      fill_in "password", with: ENV['TRIPIT_SANDBOX_ACCOUNT_PASSWORD']
      click_button "Sign In"

      # Sometimes we won't get an allow button for some reason
      # Might be something that TripIt is doing server-side.
      begin
        click_button "Allow"
      rescue
      end

      # Weird bug with Capybara where it wraps JSON in a HTML block.
      expected_response = "<html><head></head><body>\
<pre style=\"word-wrap: break-word; white-space: pre-wrap;\">\
{\"status\":\"ok\",\"token_changed\":false}\
</pre></body></html>"
      expect(page.html).to match expected_response
    end
  end

  context "Step 3" do
    it "Should provide me with a token", :integration do
      response = HTTParty.get("#{$api_gateway_url}/getToken", {
        headers: { 'x-api-key': $test_api_key }
      })
      expect(response.code.to_i).to eq 200
      expect(JSON.parse(response.body)['token']).not_to be nil
      expect(JSON.parse(response.body)['token_secret']).not_to be nil
    end
  end
end
