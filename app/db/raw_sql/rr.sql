with total_earnings as
(
    select o.token_id, o.contract_address, o.collection_slug, o.buyer, extract(epoch from (coalesce(o.sell_time, now()) - o.buy_time)) / (3600 * 24) as days_held, t.symbol, (sum(t.price / pow(10, t.decimals))) as earnings
    from nft_ownership o
    join erc20_transfers t
    on t.buyer = o.buyer
    where t.event_timestamp between o.buy_time and o.sell_time
    group by o.contract_address, o.token_id, o.buyer, o.buy_time, o.sell_time, t.symbol
)
select token_id, contract_address, collection_slug, symbol, avg(earnings / days_held) as roi
from total_earnings
group by token_id, contract_address, symbol, collection_slug
order by contract_address, token_id;