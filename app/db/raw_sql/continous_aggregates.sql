create materialized view if not exists public.collection_dynamic_hourly
with (timescaledb.continuous) as
select
    time_bucket('1 hour', event_timestamp) as hour,
    min(event_timestamp) as event_timestamp,
    collection_slug,
    avg(sales) as sales,
    avg(volume) as volume,
    avg(floor_price) as floor_price,
    floor_price_currency,
    avg(average_price)  as average_price,
    -- avg(uaw) as uaw,
    avg(total_wallets) as total_wallets
from collection_dynamic
group by hour, collection_slug, floor_price_currency;

create materialized view if not exists public.collection_dynamic_daily
with (timescaledb.continuous) as
select
    time_bucket('1 day', event_timestamp) as hour,
    min(event_timestamp) as event_timestamp,
    collection_slug,
    avg(sales) as sales,
    avg(volume) as volume,
    avg(floor_price) as floor_price,
    floor_price_currency,
    avg(average_price)  as average_price,
    -- avg(uaw) as uaw,
    avg(total_wallets) as total_wallets
from collection_dynamic
group by hour, collection_slug, floor_price_currency;

create materialized view if not exists public.collection_dynamic_monthly
with (timescaledb.continuous) as
select
    time_bucket('1 month', event_timestamp) as bucket,
    min(event_timestamp) as event_timestamp,
    collection_slug,
    avg(sales) as sales,
    avg(volume) as volume,
    avg(floor_price) as floor_price,
    floor_price_currency,
    avg(average_price)  as average_price,
    -- avg(uaw) as uaw,
    avg(total_wallets) as total_wallets
from collection_dynamic
group by hour, collection_slug, floor_price_currency;


