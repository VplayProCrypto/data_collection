create or replace function insert_nft_ownership()
returns trigger
as $$
declare
    total_quantity int;
    prev_rec record;
begin
    select sum(quantity) into total_quantity
    from nft_ownership
    where token_id = new.token_id
        and contract_address = new.contract_address
        and buyer = new.seller
        and sell_time is null;
    
    select * into prev_rec
    from nft_ownership
    where token_id = new.token_id
        and contract_address = new.contract_address
        and buyer = new.seller
        and sell_time is null
    limit 1;

    update nft_ownership
    set sell_time = new.event_timestamp
    where token_id = new.token_id
        and contract_address = new.contract_address
        and buyer = new.seller
        and sell_time is null;
    
    RAISE NOTICE 'New Event: token_id=%, contract_address=%, seller=%, buyer=%, event_timestamp=%, quantity=%', 
    NEW.token_id, NEW.contract_address, NEW.seller, NEW.buyer, NEW.event_timestamp, NEW.quantity;

    insert into nft_ownership (token_id, contract_address, seller, buyer, buy_time, sell_time, collection_slug, transaction_hash, game_id, quantity)
    values (new.token_id, new.contract_address, new.seller, new.buyer, new.event_timestamp,
            null, new.collection_slug, new.transaction_hash, new.game_id, new.quantity);
    

    if total_quantity > new.quantity then
        insert into nft_ownership (token_id, contract_address, seller, buyer, buy_time, sell_time, collection_slug, transaction_hash, game_id, quantity)
        values (prev_rec.token_id, prev_rec.contract_address, null, prev_rec.buyer, new.event_timestamp,
                null, prev_rec.collection_slug, prev_rec.transaction_hash, prev_rec.game_id, total_quantity - new.quantity);
    end if;
    return new;
end$$
language plpgsql;

CREATE TRIGGER update_nft_ownership
  AFTER INSERT ON nft_events
  FOR EACH ROW
  EXECUTE PROCEDURE insert_nft_ownership();