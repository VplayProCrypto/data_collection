create or replace function insert_nft_ownership()
returns trigger
as $$
begin
    update nft_ownership
    set sell_time = new.event_timestamp
    where token_id = new.token_id
        and contract_address = new.contract_address
        and buyer = new.seller
        and sell_time is null;
    
    insert into nft_ownership (token_id, contract_address, seller, buyer, buy_time, sell_time, collection_slug, transaction_hash, game_id)
    values (new.token_id, new.contract_address, new.seller, new.buyer, new.event_timestamp,
            null, new.collection_slug, new.transaction_hash, new.game_id);
    return new;
end$$
language plpgsql;

