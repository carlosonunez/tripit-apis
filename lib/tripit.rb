require 'logger'
require 'tripit/health'
require 'tripit/auth'
require 'tripit/core/oauth'

module TripIt
  @logger = Logger.new(STDOUT)
  @logger.level = ENV['LOG_LEVEL'] || Logger::WARN
  def self.logger
    @logger
  end
end
