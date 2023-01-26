# Rentee Bot + Renter Bot + Listing Parser
## Running a new bot
1) Clone everything from this repo.
2) Edit `example.env` and save as `.env`.
2) Execute `docker compose up -d` to build and run bots and parser.
3) After everything is up - execute `docker exec -it villabot_all_renter_1 python3 fill_db.py` to fill a database. Change `villabot_all` part if cloned folder was renamed.

## Running a existing bot
There is already premade Compose files:

* Dev: uses @testvillarenteebot and @testvillarenterbot
* Prod: uses @villa_rental_bot and @villa_tenant_bot

To run them:
Dev: `docker compose up -d --env-file dev.env -f docker-compose.dev.yml up`
Prod: `docker compose up -d --env-file prod.env -f docker-compose.prod.yml up`

## .env details
### Telegram bots:
* `RENTEE_TOKEN` - rental/rentee Telegram bot token.
* `OWNER_TOKEN` - owner/tenant/renter Telegram bot token.
### Database:
* `POSTGRES_DB` - PostgreSQL database name.
* `POSTGRES_USER` - PostgreSQL username.
* `POSTGRES_PASSWORD` -PostgreSQL password.
* `DB_ADDRESS` - PostgreSQL address. By default - service name from docker compose (`db`).
* `DB_PORT` - PostgreSQL port. By default - `5432`.
### Parser:
* `STORAGE_IDS` - list of channels ids[^1]. Example : `STORAGE_IDS = '[-1001703670132, -1001250306088, -1001790304267]'`
* `PROXY` - list of proxies. Example: `PROXY = '["http://user:pass@ip:port", "http://user:pass@ip:port"]'`
* `SLEEP_INTERVAL` - sleep interval between parser search requests.
### Cache of bot states:
* `MONGO_HOST` - MongoDB database address.
* `MONGO_PORT` - MongoDB database port.
* `MONGO_USERNAME` - MongoDB database username.
* `MONGO_PASSWORD` - MongoDB database password.

[^1]: Since Telegram doesn't allow uploading pictures without sending them somewhere - these channels being used for "uploading" purposes. 