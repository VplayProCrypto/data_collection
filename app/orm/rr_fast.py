from sqlmodel import create_engine, Session
from sqlalchemy import text
import json

# Define the database URL
DATABASE_URL = "postgresql+psycopg2://user:password@localhost/dbname"  # Replace with your database URL

# Create the database engine
engine = create_engine(DATABASE_URL)

# Function to calculate and store NFT ROI and collection ROI for a specified game
def calculate_and_store_roi(game_id: str):
    with Session(engine) as session:
        # Step 1: Calculate ownership periods and total ERC20 tokens earned
        calculate_nft_roi_sql = f"""
        WITH ownership_periods AS (
            SELECT
                buyer,
                token_id,
                contract_address,
                collection_slug,
                buy_time,
                COALESCE(sell_time, NOW()) AS sell_time
            FROM
                public.nft_ownership
            WHERE
                game_id = :game_id
        ),
        average_buy_price AS (
            SELECT
                o.buyer,
                o.token_id,
                o.contract_address,
                o.collection_slug,
                AVG(t.price) AS avg_buy_price
            FROM
                ownership_periods o
            JOIN
                public.erc20_transfers t ON o.buyer = t.buyer
                                        AND o.collection_slug = t.collection_slug
                                        AND t.event_timestamp = o.buy_time
            GROUP BY
                o.buyer, o.token_id, o.contract_address, o.collection_slug
        ),
        total_earnings AS (
            SELECT
                o.buyer,
                o.token_id,
                o.contract_address,
                o.collection_slug,
                SUM(t.price) AS total_erc20_earned
            FROM
                ownership_periods o
            JOIN
                public.erc20_transfers t ON o.buyer = t.buyer
                                        AND o.collection_slug = t.collection_slug
                                        AND t.event_timestamp BETWEEN o.buy_time AND o.sell_time
            GROUP BY
                o.buyer, o.token_id, o.contract_address, o.collection_slug
        ),
        nft_roi AS (
            SELECT
                a.buyer,
                a.token_id,
                a.contract_address,
                a.collection_slug,
                a.avg_buy_price,
                e.total_erc20_earned,
                (e.total_erc20_earned - a.avg_buy_price) / a.avg_buy_price AS roi
            FROM
                average_buy_price a
            JOIN
                total_earnings e ON a.buyer = e.buyer
                                AND a.token_id = e.token_id
                                AND a.contract_address = e.contract_address
                                AND a.collection_slug = e.collection_slug
        )
        INSERT INTO public.nft_dynamic (collection_slug, token_id, contract_address, rr, event_timestamp)
        SELECT
            collection_slug,
            token_id,
            contract_address,
            roi,
            NOW()
        FROM
            nft_roi
        ON CONFLICT (collection_slug, token_id, contract_address, event_timestamp)
        DO UPDATE SET rr = EXCLUDED.rr, event_timestamp = EXCLUDED.event_timestamp;
        """
        session.execute(text(calculate_nft_roi_sql), {"game_id": game_id})
        session.commit()

        # Step 2: Calculate and store ROI for each collection
        calculate_and_store_collection_roi_sql = f"""
        WITH collection_rois AS (
            SELECT
                collection_slug,
                AVG(rr) AS avg_collection_roi
            FROM
                public.nft_dynamic
            WHERE
                collection_slug IN (SELECT opensea_slug FROM public.collection WHERE game_id = :game_id)
            GROUP BY
                collection_slug
        )
        INSERT INTO public.collection_dynamic (collection_slug, game_id, roi, event_timestamp)
        SELECT
            c.collection_slug,
            col.game_id,
            c.avg_collection_roi,
            NOW()
        FROM
            collection_rois c
        JOIN
            public.collection col ON c.collection_slug = col.opensea_slug
        WHERE
            col.game_id = :game_id
        ON CONFLICT (collection_slug, event_timestamp)
        DO UPDATE SET roi = EXCLUDED.roi, event_timestamp = EXCLUDED.event_timestamp;
        """
        session.execute(text(calculate_and_store_collection_roi_sql), {"game_id": game_id})
        session.commit()

# Main function to orchestrate the calculations
def main():
    # game_id = 'YOUR_GAME_ID'  # Replace with your specific game ID
    with open('../../games.json') as f:
        game_ids = json.loads(f.read()).keys()
    for i in game_ids:
        calculate_and_store_roi(i)

if __name__ == "__main__":
    main()
