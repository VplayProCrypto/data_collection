alter table nft set (
    timescale.compres,
    timescale.compres_segment_by = 'collection_slug'
);

alter table collection set (
    timescale.compres,
    timescale.compres_segment_by = 'game_id'
);

-- alter table nft set (
--     timescale.compres,
--     timescale.compres_segment_by = 'collection_slug'
-- );