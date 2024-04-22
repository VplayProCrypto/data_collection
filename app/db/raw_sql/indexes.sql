create index on public.collection_dynamic (collection_slug);
create index on public.erc20_transfers (buyer, contract_address);
create index on public.token_price (contract_address);
-- create index on public.nft_ownership (contract_address, token_id);
-- create index on public.nft_events (contract_address, token_id);