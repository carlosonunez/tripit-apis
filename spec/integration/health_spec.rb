require 'spec_helper'

describe 'TripIt API Health', :integration do
  it "Should ping back" do
    response = Net::HTTP.get_response URI("#{$api_gateway_url}/ping")
    expect(response.code.to_i).to eq 200
    expect(response.body).to eq({ message: 'sup dawg' }.to_json)
  end
end
