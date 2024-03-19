create or replace function insert_nft_ownership()
returns trigger
as $$
declare
    latest_rec record;
begin
    select * into latest_rec
    from nft_events
    where token_id = new.token_id and contract_address = new.contract_address and buyer = new.seller
    order by event_timestamp desc
    limit 1;
    
    if found then
        insert into nft_ownership (token_id, contract_address, seller, buyer, buy_time, sell_time, collection_slug)
        values (new.token_id, new.contract_address, latest_rec.seller, new.seller, latest_rec.event_timestamp,
                new.event_timestamp, new.collection_slug);
    else
        insert into nft_ownership (token_id, contract_address, seller, buyer, buy_time, sell_time, collection_slug)
        values (new.token_id, new.contract_address, latest_rec.seller, new.seller, latest_rec.event_timestamp,
                new.event_timestamp, new.collection_slug);
