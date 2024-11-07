create index idx_collection_dynamic_collection_slug on public.collection_dynamic (collection_slug);
create index idx_erc_20transfers_buyer_contract_address on public.erc20_transfers (buyer, contract_address);
create index idx_token_price_contract_address on public.token_price (contract_address);
CREATE INDEX idx_conversations_title ON conversations(title);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
-- create index on public.nft_ownership (contract_address, token_id);
-- create index on public.nft_events (contract_address, token_id);