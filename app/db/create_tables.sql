create table if not exists games_metadata (
    id serial primary key,
    name text,
    opensea_slug text unique,
    description text,
    image_url text,
    banner_image_url text,
    own text,
    category text,
    opensea_url text,
    project_url text,
    wiki_url text,
    discord_url text,
    telegram_url text,
    twitter_username text,
    instagram_username text
);

create table if not exists games_dynamic (
    id integer,
    total_supply numeric,
    volume numeric,
    sales numeric,
    average_price numeric,
    time_stamp date,
    foreign key (id) references games_metadata(id)
);

create table if not exists contracts (
    contract_address text not null unique,
    game_id integer not null,
    chain text,
    primary key (contract_address, game_id),
    foreign key (game_id) references games_metadata(id)
);

create table if not exists fees (
    game_id integer not null,
    fee float not null default 0,
    recipient text not null
);

create table if not exists nfts (
    contract_address text not null,
    token_id text not null,
    opensea_slug text,
    token_standard text,
    descp text,
    image_url text,
    metadata_url text,
    opensea_url text,
    updated_at date,
    traits jsonb,
    primary key (contract_address, token_id),
    foreign key (contract_address) references contracts(contract_address),
    foreign key (opensea_slug) references games_metadata(opensea_slug)
);

create table if not exists nft_listing (
    order_hash text primary key,
    token_id text,
    contract_address text,
    current_currency text,
    offerer text,
    current_price_val numeric,
    current_price_decimals integer,
    current_price_symbol text
);

create table if not exists events (
    order_hash text primary key,
    event_type text,
    seller text,
    buyer text,
    event_timestamp date,
    token_id text,
    contract_address text,
    foreign key (contract_address, token_id) references nfts(contract_address, token_id) 
);