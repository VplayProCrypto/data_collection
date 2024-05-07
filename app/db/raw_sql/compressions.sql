alter table nft set (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'collection_slug'
);

alter table collection set (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'game_id'
);

-- alter table nft set (
--     timescale.compres,
--     timescale.compres_segment_by = 'collection_slug'
-- );