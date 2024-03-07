select create_hypertable('nft_events', by_range('event_timestamp'));
select create_hypertable('collection_dynamic', by_range('event_timestamp'));
select create_hypertable('erc20_transfers', by_range('event_timestamp'));
select create_hypertable('token_price', by_range('event_timestamp'));
select create_hypertable('nft_ownership', by_range('buy_time'));
-- select add_dimension('nft_ownership', by_hash('collection_slug'));
-- select add_dimension('nft_events', by_hash('collection_slug'));
-- select add_dimension('collection_dynamic', by_hash('collection_slug'));
-- select add_dimension('nft_ownership', by_hash('collection_slug'));
-- select create_hypertable('nft_', '')
-- select create_hypertable('nft_', '')
-- select create_hypertable('nft_', '')