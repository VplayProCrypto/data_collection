CREATE TABLE IF NOT EXISTS public.collection
(
    opensea_slug character varying not null,
    game_name character varying,
    game_id character varying,
    name character varying(50) not null,
    description character varying not null,
    owner character varying not null,
    category character varying not null,
    is_nsfw boolean not null default false,
    opensea_url character varying,
    project_url character varying,
    wiki_url character varying,
    discord_url character varying,
    telegram_url character varying,
    twitter_url character varying,
    instagram_url character varying,
    created_date timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),
    CONSTRAINT collection_pkey primary key (opensea_slug)
);

CREATE TABLE IF NOT EXISTS public.collection_dynamic
(
    collection_slug character varying not null,
    game_id character varying,
    total_average_price double precision,
    total_supply double precision,
    total_volume double precision,
    total_num_owners integer,
    total_sales double precision,
    total_market_cap double precision,
    sales double precision,
    volume double precision,
    floor_price double precision,
    floor_price_currency character varying,
    average_price double precision,
    daily_uaw bigint,
    monthly_uaw bigint,
    total_wallets bigint,
    twitter_followers bigint,
    twitter_sentiment double precision,
    facebook_followers bigint,
    facebook_sentiment double precision,
    instagram_followers bigint,
    instagram_sentiment double precision,
    reddit_users bigint,
    reddit_sentiment double precision,
    discord_server_size bigint,
    discord_sentiment double precision,
    telegram_supergroup_size bigint,
    telgram_sentiment double precision,
    event_timestamp timestamp with time zone not null,
    CONSTRAINT collection_dynamic_pkey primary key (collection_slug, event_timestamp),
    CONSTRAINT collection_dynamic_collection_slug_fkey FOREIGN KEY (collection_slug)
        REFERENCES public.collection (opensea_slug) match simple
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

CREATE TABLE IF NOT EXISTS public.contract
(
    collection_slug character varying not null,
    contract_address character varying not null,
    chain character varying not null,
    CONSTRAINT contract_pkey primary key (contract_address, chain),
    CONSTRAINT contract_collection_slug_fkey FOREIGN KEY (collection_slug)
        REFERENCES public.collection (opensea_slug) match simple
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

CREATE TABLE IF NOT EXISTS public.erc20_transfers
(
    buyer character varying not null,
    seller character varying not null,
    contract_address text not null,
    price double precision not null,
    symbol character varying not null,
    decimals integer not null,
    transaction_hash character varying not null,
    event_timestamp timestamp with time zone not null,
    collection_slug text,
    CONSTRAINT erc20_transfers_pkey primary key (transaction_hash, event_timestamp)
);

CREATE TABLE IF NOT EXISTS public.fee
(
    collection_slug character varying not null,
    fee double precision not null,
    recipient character varying not null,
    CONSTRAINT fee_pkey primary key (collection_slug, recipient),
    CONSTRAINT fee_collection_slug_fkey FOREIGN KEY (collection_slug)
        REFERENCES public.collection (opensea_slug) match simple
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

CREATE TABLE IF NOT EXISTS public.nft
(
    collection_slug character varying not null,
    game_id character varying,
    token_id character varying not null,
    contract_address character varying not null,
    token_standard character varying not null,
    name character varying,
    description character varying,
    image_url character varying,
    metadata_url character varying,
    opensea_url character varying,
    updated_at timestamp with time zone,
    is_nsfw boolean not null default false,
    is_disabled boolean not null default false,
    traits jsonb,
    CONSTRAINT nft_pkey primary key (token_id, contract_address),
    CONSTRAINT nft_opensea_slug_fkey FOREIGN KEY (collection_slug)
        REFERENCES public.collection (opensea_slug) match simple
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

CREATE TABLE IF NOT EXISTS public.payment_tokens
(
    collection_slug character varying not null,
    contract_address character varying not null,
    symbol character varying,
    decimals integer not null,
    chain character varying not null,
    CONSTRAINT payment_tokens_pkey primary key (collection_slug, contract_address),
    CONSTRAINT payment_tokens_collection_slug_fkey FOREIGN KEY (collection_slug)
        REFERENCES public.collection (opensea_slug) match simple
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

CREATE TABLE IF NOT EXISTS public.nft_events
(
    transaction_hash character varying,
    marketplace character varying,
    marketplace_address character varying,
    block_number bigint,
    order_hash character varying,
    event_type text,
    token_id character varying not null,
    contract_address character varying not null,
    collection_slug character varying not null,
    game_id character varying not null,
    seller character varying not null,
    buyer character varying,
    quantity integer default 1,
    price_val character varying,
    price_currency character varying,
    price_decimals character varying,
    event_timestamp timestamp with time zone not null,
    CONSTRAINT nft_events_pkey primary key (contract_address, token_id, event_timestamp)
    -- CONSTRAINT nft_events_token_id_fkey FOREIGN KEY (token_id, contract_address)
    --     REFERENCES public.nft (token_id, contract_address) match simple
    --     ON UPDATE NO ACTION
    --     ON DELETE NO ACTION
);

CREATE TABLE IF NOT EXISTS public.token_price
(
    contract_address character varying not null,
    eth_price double precision not null,
    usdt_price double precision not null,
    usdt_conversion_price double precision,
    eth_conversion_price double precision,
    event_timestamp timestamp with time zone not null,
    CONSTRAINT token_price_pkey primary key (contract_address, event_timestamp)
);

CREATE TABLE IF NOT EXISTS public.nft_ownership
(
    buyer character varying,
    seller character varying,
    token_id character varying not null,
    contract_address character varying not null,
    transaction_hash character varying not null,
    buy_time timestamp with time zone not null,
    quantity integer default 1,
    sell_time timestamp with time zone,
    collection_slug character varying not null,
    game_id character varying not null,
    CONSTRAINT nft_ownership_pkey primary key (contract_address, token_id, buyer, buy_time)
    -- CONSTRAINT nft_ownership_token_id_fkey FOREIGN KEY (token_id, contract_address)
    --     REFERENCES public.nft (token_id, contract_address) match simple
    --     ON UPDATE NO ACTION
    --     ON DELETE NO ACTION
);

CREATE TABLE IF NOT EXISTS public.nft_dynamic
(
    collection_slug character varying not null,
    token_id character varying not null,
    contract_address character varying not null,
    rr numeric,
    event_timestamp timestamp with time zone not null default now(),
    CONSTRAINT nft_dynamic_pk primary key (contract_address, token_id, event_timestamp)
    -- CONSTRAINT nft_dynamic_token_id_fkey FOREIGN KEY (token_id, contract_address)
    --     REFERENCES public.nft (token_id, contract_address) match simple
    --     ON UPDATE NO ACTION
    --     ON DELETE NO ACTION
);

CREATE TABLE IF NOT EXISTS public.nft_offers
(
    order_hash character varying not null,
    event_type text,
    token_id character varying not null,
    contract_address character varying not null,
    collection_slug character varying not null,
    game_id character varying not null,
    seller character varying not null,
    quantity integer default 1,
    price_val character varying,
    price_currency character varying,
    price_decimals character varying,
    start_date timestamp with time zone,
    expiration_date timestamp with time zone,
    event_timestamp timestamp with time zone not null,
    CONSTRAINT nft_offers_pkey primary key (contract_address, token_id, event_timestamp)
--     CONSTRAINT nft_offers_token_id_fkey FOREIGN KEY (token_id, contract_address)
--         REFERENCES public.nft (token_id, contract_address) match simple
--         ON UPDATE NO ACTION
--         ON DELETE NO ACTION
);

CREATE TABLE IF NOT EXISTS public.nft_listings
(
    order_hash character varying not null,
    token_id character varying not null,
    contract_address character varying not null,
    collection_slug character varying not null,
    game_id character varying not null,
    seller character varying not null,
    price_val character varying,
    price_currency character varying,
    price_decimals character varying,
    start_date timestamp with time zone,
    expiration_date timestamp with time zone,
    event_timestamp timestamp with time zone not null,
    CONSTRAINT nft_listings_pkey primary key (contract_address, token_id, event_timestamp)
    -- CONSTRAINT nft_listings_token_id_fkey FOREIGN KEY (token_id, contract_address)
    --     REFERENCES public.nft (token_id, contract_address) match simple
    --     ON UPDATE NO ACTION
    --     ON DELETE NO ACTION
);