insert into games_metadata (id, name, opensea_slug, description, image_url, banner_image_url, own,
                    category, opensea_url, project_url, wiki_url, discord_url, telegram_url, twitter_username, instagram_username)
                    values (:collection, :name, :description, :image_url, :banner_image_url, :owner, :category, :opensea_url, :project_url, :wiki_url, :discord_url, 
                    :telegram_url, :twitter_username, :instagram_username)
