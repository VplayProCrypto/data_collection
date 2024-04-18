## VPLAY Backend

## Server to monitor for user data POST requests fro mthe front end to analyze data and integrate it into TimescaleDB, periodically update TimescaleDB, run ML and data analytics

### Template from from https://github.com/docker/awesome-compose/tree/master/fastapi

# Important Files

`api_requests`: contains classes for making requests to apis. Currently Opensea and EtherScan
`transform`: Uses `api_requests` to get the data and transforms it into format that db can injest. Also masks where the data is coming from.
`postgre_injector_orm`: contains injector functions
`games.json`: Contains mapping from game_id to game_names. game_id is needed because some games have many collections.

# Important Folders

`next_page`: folder stores the next page for nfts apis. Add folders as needed
`raw_sql`: raw sql commands for tables.
