# tripit-apis

A collection of TripIt functions that I use for various things.

This is designed to run entirely in AWS Lambda.

## How to deploy

1. Create a `.env` from `.env.example` and fill it out.
2. Source common bash aliases: `source bash_aliases`
3. Run unit tests: `unit`
4. Run integration tests (uses AWS; should be free): `integration`
5. Deploy to your AWS account: `ENVIRONMENT=production deploy`
