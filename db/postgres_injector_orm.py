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