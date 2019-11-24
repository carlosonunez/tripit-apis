require 'capybara'
require 'capybara/dsl'

module Helpers
  module TripIt
    module OAuth
      # TripIt apps are required to have their callback URIs defined in their
      # application settings in order for OAuth to redirect users properly.
      # However, AWS API Gateway generates random FQDNs from which Lambdas
      # are served, and using a custom domain (like we do for production deploys)
      # requires a CloudFront distribution to back it, which can take
      # up to 40 minutes to deploy/update.
      #
      # Instead, we'll automate updating the callback URI with Selenium.
      def self.update_callback_uri!(callback_uri:)
        include Capybara::DSL
        session = Capybara::Session.new :selenium
        session.visit "https://#{ENV['TRIPIT_WORKSPACE_NAME']}.tripit.com/signin"
        session.fill_in "email", with: ENV['TRIPIT_SANDBOX_ACCOUNT_EMAIL']
        session.fill_in "password", with: ENV['TRIPIT_SANDBOX_ACCOUNT_PASSWORD']
        session.click_button "signin_btn"

        session.visit "https://api.tripit.com/apps/APDPV4M54/oauth?"
        session.find('button[data-qa="url_delete"]').click
        session.click_button "Add New Redirect URL"
        session.find('input[data-qa="app_unfurl_domain"]').fill_in \
          with: callback_uri
        session.click_button "Add"
        session.click_button "Save URLs"
      end
    end
  end
end
