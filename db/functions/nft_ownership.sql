-- FUNCTION: public.get_nft_ownership(text)

-- DROP FUNCTION IF EXISTS public.get_nft_ownership(text);

CREATE OR REPLACE FUNCTION public.get_nft_ownership(
	collection_slug text)
    RETURNS TABLE(token_id text, contract_address text, seller text, buyer text, buy_time numeric, sell_time numeric) 
    -- LANGUAGE 'plpgsql'
    -- COST 100
    -- VOLATILE PARALLEL UNSAFE
    -- ROWS 1000

AS $BODY$
begin
    return query
    with nft_events as (
        select ns.token_id, ns.buyer, ns.seller, ns.event_timestamp, ns.contract_address
        from nft_sale as ns
        where ns.collection_slug = collection_slug
        union
        select nt.token_id, nt.buyer, nt.seller, nt.event_timestamp, nt.contract_address
        from nft_transfer as nt
        where nt.collection_slug = collection_slug
    ), sequenced_sales as (
        select
            *,
            lead(events.event_timestamp) over (partition by events.token_id, events.contract_address order by events.event_timestamp) as next_event_timestamp,
            lead(events.buyer) over (partition by events.token_id, events.contract_address order by events.event_timestamp) as next_buyer
        from nft_events as events
    ),
    buys as (
        select
            *,
            seq_sales.next_event_timestamp as sell_time,
            seq_sales.next_buyer as buyer_a
        from sequenced_sales as seq_sales
        where seq_sales.buyer <> seq_sales.next_buyer -- Assuming the buyer changes on a sell
    )
    select
        buys.token_id,
        buys.contract_address,
        buys.buyer as seller,
        buys.buyer_a as buyer,
        buys.event_timestamp as buy_time,
        buys.sell_time
    from buys as buys
    where buys.event_timestamp < sell_time;
end; 
$BODY$;

ALTER FUNCTION public.get_nft_ownership(text)
    OWNER TO postgres;
