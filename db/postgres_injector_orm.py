from datetime import datetime
from typing import List, Set
from sqlalchemy import text, func, create_engine, inspect
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError
from models import Collection, CollectionDynamic, Contract, Nft, \
    NftListing, NftOwnership, NftSale, NftTransfer, Erc20Transfer, PaymentTokens, TokenPrice
import psycopg2
from api_requests import OpenSea

class Injector:
    def __init__(self, username: str = None, password: str = None, port: str = None, database: str = None, host: str = None):
        self.username = 'postgres'
        self.port = '5432'
        self.database = 'local'
        self.password = 'postgres'
        if not username:
            self.url = f'postgresql+psycopg2://{self.username}:{self.password}@localhost:{self.port}/{self.database}'
        else:
            self.url = f'postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}'
        
        self.engine = create_engine(self.url)
    
    def _save_next_page(self, file_path: str, next_page_link: str):
        """ utility to save the next page link from previous response. To start from the new page every time. Reduces number of requests made.
        :param file_path: path of the file to save the next page link
        :param next_page_link: link to te next page
        """

        with open(file_path, 'a') as f:
            f.write(next_page_link)
            f.write('\n')
    
    def map_opensea_collection(self, collection_data: dict):
        return {
            'opensea_slug': collection_data['collection'],
            'name': collection_data['name'],
            'description': collection_data['description'],
            'owner': collection_data['owner'],
            'category': collection_data['category'],
            'is_nsfw': collection_data['is_nsfw'],
            'opensea_url': collection_data['opensea_url'],
            'project_url': collection_data['project_url'],
            'wiki_url': collection_data['wiki_url'],
            'discord_url': collection_data['discord_url'],
            'telegram_url': collection_data['telegram_url'],
            'twitter_url': collection_data['twitter_username'],
            'instagram_url': collection_data['instagram_username'],
            'updated_at': collection_data['updated_at'],
        }
    
    def map_opensea_nft_event(event_data: dict):
        assert(isinstance(event_data, dict))
        mapped_event = {
            'transaction_hash': None,
            'token_id': None,
            'contract_address': None,
            'event_timestamp': None,
            'buyer': None,
            'seller': None,
            'price_val': None,
            'price_currency': None,
            'price_decimals': None,
            'start_date': None,
            'expiration_date': None,
            'event_type': None,
            'collection_slug': None
        }
        mapped_event['transaction_hash'] = event_data['transaction']
        mapped_event['event_type'] = event_data['event_type']
        mapped_event['event_timestamp'] = event_data['event_timestamp']
        mapped_event['quantity'] = event_data['quantity']
        if mapped_event['event_type'] == 'sale':
            mapped_event['token_id'] = event_data['nft']['identifier']
            mapped_event['collection_slug'] = event_data['nft']['collection']
            mapped_event['buyer'] = event_data['buyer']
            mapped_event['seller'] = event_data['seller']
            mapped_event['price_val'] = event_data['payment']['quantity']
            mapped_event['price_symbol'] = event_data['payment']['symbol']
            mapped_event['price_decimals'] = event_data['payment']['decimals']
        elif mapped_event['event_type'] == 'transfer':
            mapped_event['token_id'] = event_data['nft']['identifier']
            mapped_event['collection_slug'] = event_data['nft']['collection']
            mapped_event['buyer'] = event_data['to_address']
            mapped_event['seller'] = event_data['from_address']
        elif mapped_event['event_type'] == 'order':
            mapped_event['event_type'] = 'listing'
            mapped_event['seller'] = event_data['maker']
            mapped_event['start_date'] = datetime.fromtimestamp(event_data['start_date'])
            t = event_data['expiration_date']
            mapped_event['expiration_date'] = datetime.fromtimestamp(t) if t else None
        
        return mapped_event
    
    def map_opensea_contract(contract_data: dict, collection_slug: str):
        return {
            'collection_slug': collection_slug,
            'contract_address': contract_data['address'],
            'chain': contract_data['chain']
        }
    
    def map_etherscan_erc20_transfer(transfer_data: dict, collection_slug: str):
        return {
            'buyer': transfer_data['to'],
            'seller': transfer_data['from'],
            'contract_address': transfer_data['contractAddress'],
            'price': transfer_data['value'],
            'symbol': transfer_data['tokenSymbol'],
            'decimals': int(transfer_data['tokenDecimal']),
            'transaction_hash': transfer_data['hash'],
            'event_timestamp': datetime.fromtimestamp(int(transfer_data['timeStamp'])),
            'collection_slug': collection_slug,
        }
    
    def map_opensea_fee(fee_data: dict, collection_slug: str):
        return {
            'collection_slug': collection_slug,
            'fee': fee_data['fee'],
            'recipient': fee_data['recipient'],
        }
    
    def map_opensea_nft(nft_data):
        return {
            'collection_slug': nft_data['collection'],
            'token_id': nft_data['identifier'],
            'contract_address': nft_data['contract'],
            'name': nft_data['name'],
            'description': nft_data['description'],
            'image_url': nft_data['image_url'],
            'metadata_url': nft_data['metadata_url'],
            'opensea_url': nft_data['opensea_url'],
            'is_nsfw': nft_data['is_nsfw'],
            'is_disabled': nft_data['is_disabled'],
            # 'traits': nft_data[''],
            'token_standard': nft_data['token_standard'],
            'updated_at': datetime.fromisoformat(nft_data['updated_at'])
        }
    
    def map_payment_tokens(token_data: dict):
        return {
            'collection_slug': token_data['collection_slug'],
            'contract_address': token_data['contract_address'],
            'symbol': token_data['symbol'],
            'decimals': token_data['decimals'],
            'chain': token_data['chain'],
        }
    
    def map_token_price(price_data: dict):
        return {
            'contract_address': price_data[''],
            'eth_price': price_data[''],
            'usdt_price': price_data[''],
            'usdt_conversion_price': price_data[''],
            'eth_conversion_price': price_data[''],
            'event_timestamp': datetime.fromtimestamp(price_data[''])
        }
    
    def raw_sql(self, file_path: str):
        with Session(self.engine) as session:
            with open(file_path, mode = 'r') as f:
                r = f.read()
            session.execute(text(r))
            session.commit()
    
    def _remove_duplicates(self, new_data, index_columns):
        unique_combinations = set()
        cleaned_data = []

        for item in new_data:
            # Check if the item has None in any of the index_columns
            if any(item[column] is None for column in index_columns):
                continue  # Skip this item
            
            # Create a tuple of values for the item based on index_columns
            values_tuple = tuple(item[column] for column in index_columns)
            
            # Check if we've already seen this combination
            if values_tuple not in unique_combinations:
                unique_combinations.add(values_tuple)
                cleaned_data.append(item)

        return cleaned_data
    
    def get_insert_smt(self, new_data: List[dict], model, upsert: bool):
        insert_smt = insert(model).values(new_data)
        if upsert:
            index_columns = [key.name for key in inspect(model).primary_key]
            print(index_columns)
            smt = insert_smt.on_conflict_do_update(index_elements=index_columns, set_=insert_smt.excluded)
        else:
            smt = insert_smt.on_conflict_do_nothing(index_elements = index_columns)
        return smt


    def bulk_insert(self, new_data: List[dict], model, upsert: bool = False):
        with Session(self.engine) as session:
            try:
                session.execute(self.get_insert_smt(new_data, model, upsert))
                session.commit()
            except ProgrammingError as e:
                if isinstance(e.orig, psycopg2.errors.InFailedSqlTransaction):
                    # Rollback the session to exit the aborted state
                    session.rollback()
                    index_columns = [key.name for key in inspect(model).primary_key]
                    without_duplicates = self._remove_duplicates(new_data, index_columns)
                    session.execute(self.get_insert_smt(without_duplicates, model, upsert))
                    session.commit()
                else:
                    raise e
            except SQLAlchemyError as e:
                # This catches other SQLAlchemy-related errors
                session.rollback()  # Ensure the session is rolled back on any error
                print("SQLAlchemy error occurred: ", e)
                raise e

def main():
    injector = Injector(username='tsdbadmin', password='m9u74pu73bg9fdxi', host='v4ob0qdj5t.y1jft9lh0x.tsdb.cloud.timescale.com', port='35641', database='tsdb')
    # injector.raw_sql('./raw_sql/tables.sql')
    # injector.raw_sql('./raw_sql/hypertables.sql')
    injector.raw_sql('./raw_sql/indexes.sql')

if __name__ == "__main__":
    main()