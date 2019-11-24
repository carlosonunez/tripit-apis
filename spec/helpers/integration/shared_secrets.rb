module Helpers
  module Integration
    module SharedSecrets
      def self.create_secret_path(secret_name:)
        secret_folder = ENV['SHARED_SECRETS_FOLDER'] || '/secrets'
        raise "Secrets folder not found" if !Dir.exist? secret_folder
        "#{secret_folder}/#{secret_name}"
      end

      def self.read_secret(secret_name:)
        secret_path = create_secret_path secret_name: secret_name
        raise "Secret not found at: #{secret_path}" if !File.exist? secret_path
        File.read secret_path
      end

      def self.write_secret(secret_name:, content:)
        File.open((create_secret_path secret_name: secret_name), 'w') do |file|
          file.write content
        end
      end

      def self.remove_secret(secret_name:)
        File.delete (create_secret_path secret_name: secret_name) \
          if File.exist? (create_secret_path secret_name: secret_name)
      end
    end
  end
end
