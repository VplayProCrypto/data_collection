# data_collection

Repo to collect and process data from Open Mesh API

### open mesh websockets

Subscribe to them for live updates from the ethereum chain
We need to have a cache of these events to display in our dashboards and update them as they come in
Doesn't seem to work at the moment

### pythia?

This seems to be where the historical data is stored in a Postgres database.
Perhaps we need to query their database for the historical records?
There is supposed to be a REST API and GraphQL that we can use but I can't find a reference to it.
Hasn't been updated in a few months.


### curl

curl -X GET "https://apis.dappradar.com/v2/dapps" \
 -H "accept: application/json"\
 -H "x-api-key: InrjMd9Bxc6geuaIus7lm2wIDHqjwr3575qt6hYk" \
