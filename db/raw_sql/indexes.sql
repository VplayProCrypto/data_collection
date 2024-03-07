create index on public.collection_dynamic (collection_slug);
create index on public.erc20_transfers (contract_address);
create index on public.token_price (contract_address);
create index on public.nft_ownership (collection_slug);
create index on public.nft_events (collection_slug);