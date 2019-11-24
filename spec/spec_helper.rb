require 'rspec'
require 'httparty'
require 'capybara'
require 'capybara/dsl'
require 'selenium-webdriver'
require 'tripit-api'
require 'timeout'
Dir.glob('/app/spec/helpers/**/*.rb') do |file|
  require_relative file
end

# Test setup and teardown is done entirely through docker-compose to
# reduce the number of  moving parts. Since docker-compose runs all of its dependent services
# in parallel, we need to manually synchronize the state of our tests and
# manually await certain data becoming available.
RSpec.configure do |config|
  config.include Capybara::DSL, :integration => true
  config.before(:all, :unit => true) do
    ENV['APP_AWS_ACCESS_KEY_ID'] = 'fake'
    ENV['APP_AWS_SECRET_ACCESS_KEY'] = 'fake'
    if !$dynamodb_mocking_started
      Helpers::Aws::DynamoDBLocal.start_mocking!
      puts "Waiting 60 seconds for local DynamoDB instance to become availble."
      seconds_elapsed = 0
      loop do
        raise "DynamoDB local not ready." if seconds_elapsed == 60
        break if Helpers::Aws::DynamoDBLocal.started?
        seconds_elapsed += 1
        sleep(1)
      end
      $dynamodb_mocking_started = true
    end
  end

  config.before(:all, :integration => true) do
    ['SELENIUM_HOST', 'SELENIUM_PORT'].each do |required_selenium_env_var|
      raise "Please set #{required_selenium_env_var}" if ENV[required_selenium_env_var].nil?
    end

    $api_gateway_url = ENV['API_GATEWAY_URL'] || Helpers::Integration::HTTP.get_endpoint
    raise "Please define API_GATEWAY_URL as an environment variable or \
run 'docker-compose run --rm integration-setup'" \
      if $api_gateway_url.nil? or $api_gateway_url.empty?

    $test_api_key =
      Helpers::Integration::SharedSecrets.read_secret(secret_name: 'api_key') ||
        raise('Please create the "api_key" secret.')

    Capybara.run_server = false
    Capybara.register_driver :selenium do |app|
      Capybara::Selenium::Driver.new(
        app,
        browser: :remote,
        url: "http://#{ENV['SELENIUM_HOST']}:#{ENV['SELENIUM_PORT']}/wd/hub",
        desired_capabilities: Selenium::WebDriver::Remote::Capabilities.chrome(
          "chromeOptions" => {
            "args" => ['--no-default-browser-check']
          }
        )
      )
    end
    Capybara.default_driver = :selenium

    if !$callback_updated
      if ENV['DISABLE_TRIPIT_CALLBACK_UPDATING'] != 'true'
        puts "INFO: Updating TripIt callback URIs."
        if !Helpers::TripIt::OAuth.update_callback_uri! \
          callback_uri: "#{$api_gateway_url}/callback"
          raise "Unable to update TripIt callback URIs; stopping early to prevent later failures."
        end
        $callback_updated = true
      end
    end
  end
end
