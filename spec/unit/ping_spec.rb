require 'spec_helper'

describe 'TripIt API Basics' do
  it 'Should ping back', :unit do
    expected_response = {
      body: { message: 'sup dawg' }.to_json,
      statusCode: 200
    }
    expect(TripItAPI::Health.ping).to eq expected_response
  end
end
