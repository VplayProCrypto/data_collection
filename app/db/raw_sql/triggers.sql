create or replace function insert_nft_ownership()
returns trigger
as $$
begin
    update nft_ownership
    set sell_time = new.event_timestamp
    where token_id = new.token_id
        and contract_address = new.contract_address
        and buyer = new.seller
        and sell_time is null;
    
    insert into nft_ownership (token_id, contract_address, seller, buyer, buy_time, sell_time, collection_slug, transaction_hash, game_id)
    values (new.token_id, new.contract_address, new.seller, new.buyer, new.event_timestamp,
            null, new.collection_slug, new.transaction_hash, new.game_id);
    return new;
end$$
language plpgsql;




CREATE OR REPLACE FUNCTION update_leaderboards()
RETURNS TRIGGER AS $$
DECLARE
  twitter_rank INTEGER;
  discord_rank INTEGER;
  telegram_rank INTEGER;
BEGIN
  -- Update twitter_leaderboard
  INSERT INTO public.twitter_leaderboard (collection_slug, twitter_followers)
  VALUES (NEW.collection_slug, NEW.twitter_followers)
  ON CONFLICT (collection_slug) DO UPDATE
    SET twitter_followers = NEW.twitter_followers;

  -- Update discord_leaderboard
  INSERT INTO public.discord_leaderboard (collection_slug, discord_server_size)
  VALUES (NEW.collection_slug, NEW.discord_server_size)
  ON CONFLICT (collection_slug) DO UPDATE
    SET discord_server_size = NEW.discord_server_size;

  -- Update telegram_leaderboard
  INSERT INTO public.telegram_leaderboard (collection_slug, telegram_supergroup_size)
  VALUES (NEW.collection_slug, NEW.telegram_supergroup_size)
  ON CONFLICT (collection_slug) DO UPDATE
    SET telegram_supergroup_size = NEW.telegram_supergroup_size;

  -- Get the ranks for the current collection
  SELECT rank INTO twitter_rank
  FROM (
    SELECT collection_slug, rank() OVER (ORDER BY twitter_followers DESC) AS rank
    FROM public.twitter_leaderboard
  ) AS subquery
  WHERE collection_slug = NEW.collection_slug;

  SELECT rank INTO discord_rank
  FROM (
    SELECT collection_slug, rank() OVER (ORDER BY discord_server_size DESC) AS rank
    FROM public.discord_leaderboard
  ) AS subquery
  WHERE collection_slug = NEW.collection_slug;

  SELECT rank INTO telegram_rank
  FROM (
    SELECT collection_slug, rank() OVER (ORDER BY telegram_supergroup_size DESC) AS rank
    FROM public.telegram_leaderboard
  ) AS subquery
  WHERE collection_slug = NEW.collection_slug;

  -- Update the rank columns in the collection_dynamic table
  UPDATE public.collection_dynamic
  SET twitter_rank = twitter_rank,
      discord_rank = discord_rank,
      telegram_rank = telegram_rank
  WHERE collection_slug = NEW.collection_slug
    AND event_timestamp = NEW.event_timestamp;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for updating leaderboards on INSERT or UPDATE
CREATE TRIGGER update_leaderboards_trigger
AFTER INSERT OR UPDATE ON public.collection_dynamic
FOR EACH ROW
EXECUTE FUNCTION update_leaderboards();