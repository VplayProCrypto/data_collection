create or replace function insert_nft_ownership()
returns trigger
as $$
begin
    update nft_ownership
    set sell_time = new.event_timestamp
    where token_id = new.token_id and contract_address = new.contract_address and buyer = new.seller and buy_time
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
    end if;
    return new;
end$$
language plpgsql;