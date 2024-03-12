-- Table: public.collection

-- DROP TABLE IF EXISTS public.collection cascade;

CREATE TABLE IF NOT EXISTS public.collection
(
    opensea_slug character varying not null,
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

-- Table: public.collection_dynamic

-- DROP TABLE IF EXISTS public.collection_dynamic;

CREATE TABLE IF NOT EXISTS public.collection_dynamic
(
    collection_slug character varying not null,
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
    uaw bigint,
    total_wallets bigint,
    twitter_sentiment double precision,
    facebook_sentiment double precision,
    instagram_sentiment double precision,
    reddit_sentiment double precision,
    discord_sentiment double precision,
    event_timestamp timestamp with time zone not null,
    CONSTRAINT collection_dynamic_pkey primary key (collection_slug, event_timestamp),
    CONSTRAINT collection_dynamic_collection_slug_fkey FOREIGN KEY (collection_slug)
        REFERENCES public.collection (opensea_slug) match simple
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

-- Table: public.contract

-- DROP TABLE IF EXISTS public.contract;

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

-- Table: public.erc20_transfers

-- DROP TABLE IF EXISTS public.erc20_transfers;

CREATE TABLE IF NOT EXISTS public.erc20_transfers
(
    buyer character varying not null,
    seller character varying not null,
    contract_address character varying not null,
    price double precision not null,
    symbol character varying not null,
    decimals integer not null,
    transaction_hash character varying not null,
    event_timestamp timestamp with time zone not null,
    collection_slug text,
    CONSTRAINT erc20_transfers_pkey primary key (transaction_hash, event_timestamp)
);

-- Table: public.fee

-- DROP TABLE IF EXISTS public.fee;

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

-- Table: public.nft

-- DROP TABLE IF EXISTS public.nft;

CREATE TABLE IF NOT EXISTS public.nft
(
    collection_slug character varying not null,
    token_id character varying not null,
    contract_address character varying not null,
    token_standard character varying not null,
    name character varying not null,
    description character varying not null,
    image_url character varying not null,
    metadata_url character varying not null,
    opensea_url character varying not null,
    updated_at timestamp with time zone not null,
    is_nsfw boolean not null,
    is_disabled boolean not null,
    traits jsonb,
    CONSTRAINT nft_pkey primary key (token_id, contract_address),
    CONSTRAINT nft_opensea_slug_fkey FOREIGN KEY (collection_slug)
        REFERENCES public.collection (opensea_slug) match simple
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

-- Table: public.nft

-- DROP TABLE IF EXISTS public.nft;

-- CREATE TABLE IF NOT EXISTS public.nft
-- (
--     opensea_slug character varying not null,
--     token_id character varying not null,
--     contract_address character varying not null,
--     token_standard character varying not null,
--     name character varying not null,
--     descp character varying not null,
--     image_url character varying not null,
--     metadata_url character varying not null,
--     opensea_url character varying not null,
--     updated_at timestamp with time zone not null,
--     is_nsfw boolean not null,
--     is_disabled boolean not null,
--     traits jsonb,
--     CONSTRAINT nft_pkey primary key (token_id, contract_address),
--     CONSTRAINT nft_opensea_slug_fkey FOREIGN KEY (opensea_slug)
--         REFERENCES public.collection (opensea_slug) match simple
--         ON UPDATE NO ACTION
--         ON DELETE NO ACTION
-- );

-- Table: public.payment_tokens

-- DROP TABLE IF EXISTS public.payment_tokens;

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

-- Table: public.nft_listing

-- DROP TABLE IF EXISTS public.nft_listing;

CREATE TABLE IF NOT EXISTS public.nft_events
(
    transaction_hash character varying not null,
	event_type text,
    token_id character varying not null,
    contract_address character varying not null,
    collection_slug character varying not null,
    seller character varying not null,
	buyer character varying,
    price_val character varying,
    price_currency character varying,
    price_decimals character varying,
    start_date timestamp with time zone,
    expiration_date timestamp with time zone,
    event_timestamp timestamp with time zone not null,
    CONSTRAINT nft_listing_pkey primary key (contract_address, token_id, event_timestamp)
);


-- Table: public.token_price

-- DROP TABLE IF EXISTS public.token_price;

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

-- Table: public.nft_ownership

-- DROP TABLE IF EXISTS public.nft_ownership;

CREATE TABLE IF NOT EXISTS public.nft_ownership
(
    buyer character varying not null,
    seller character varying not null,
    token_id character varying not null,
    contract_address character varying not null,
    transaction_hash character varying not null,
    buy_time timestamp with time zone not null,
    sell_time timestamp with time zone not null,
    collection_slug character varying not null,
    CONSTRAINT nft_ownership_pkey primary key (contract_address, token_id, buy_time)
);

create table if not exists public.nft_dynamic
(
    collection_slug character varying not null,
    token_id character varying not null,
    contract_address character varying not null,
    rr numeric,
    event_timestamp timestamp with time zone not null default now(),
    constraint nft_dynamic_pk primary key (contract_address, token_id, event_timestamp)
);
