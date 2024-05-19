from datetime import datetime
from typing import List, Set
from sqlalchemy import text, func, create_engine, inspect, select
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError
from .models import Collection, CollectionDynamic, Contract, NFT, NFTEvent, \
    NftOwnership, ERC20Transfer, PaymentToken, TokenPrice, Fee
import psycopg2
import argparse
from .transform import Mapper
import time
import json

class Injector:
    def __init__(self, username: str = None, password: str = None, port: str = None, database: str = None, host: str = None, eth_api_key: str = None, alchemy_api_key: str = None):
        self.username = 'tsdbadmin'
        self.port = '32026'
        self.database = 'tsdb'
        self.password = 'km8en9w8a96ghdtl'
        self.host = 'busvxhxzr1.b505mpo6st.tsdb.cloud.timescale.com'
        if not username:
            self.url = f'postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}'
        else:
            self.url = f'postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}'
        
        self.engine = create_engine(self.url)
        self.mapper = Mapper(eth_api_key = eth_api_key, alchemy_api_key = alchemy_api_key)
    
    def _save_next_page(self, file_path: str, next_page_link):
        """ utility to save the next page link from previous response. To start from the new page every time. Reduces number of requests made.
        :param file_path: path of the file to save the next page link
        :param next_page_link: link to te next page
        """

        if isinstance(next_page_link, str):
            next_page_link = [next_page_link]
        
        with open(file_path, 'a') as f:
            for i in next_page_link:
                if i is not None:
                    f.write(i)
                    f.write('\n')
    
    
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
        index_columns = [key.name for key in inspect(model).primary_key]
        if upsert:
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
    
    def insert_collection(self, collection_slug: str):
        data = self.mapper.get_collection(collection_slug)
        # print(data.keys())
        collection = Collection(**data['collection'])
        # print(collection)
        for i in data['fees']:
            collection.fees.append(Fee(**i))
        # print(collection.fees)
        for i in data['contracts']:
            collection.contracts.append(Contract(**i))
        # print(collection.contracts)
        try:
            with Session(self.engine) as session:
                session.merge(collection)
                session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e
    
    def insert_nfts(self, collection_slug: str, num_pages: int = None):
        next_page_file = f'../next_page/opensea/{collection_slug}.txt'
        try:
            with open(next_page_file, 'r') as f:
                next_page = f.readlines()[-1]
                print(next_page)
        except FileNotFoundError or FileExistsError as e:
            next_page = None
        
        if num_pages:
            r = self.mapper.get_nfts_for_collection(collection_slug, num_pages = num_pages, next_page = next_page)
            nfts = r['nfts']
            next_pages = r['next_pages']
            if len(nfts) < 1:
                print("All nfts retirved")
                return
            try:
                t = time.time()
                self.bulk_insert(nfts, Nft)
                self._save_next_page(next_page_file, next_pages)
                print(f"saved pages {len(nfts)}. Time taken: {time.time() - t} seconds")
            except Exception as e:
                raise e
        else:
            saved_pages: int = 0
            while True:
                r = self.mapper.get_nfts_for_collection(collection_slug, num_pages = 1, next_page = next_page)
                nfts = r['nfts']
                # print(nfts[:2])
                next_pages = r['next_pages']
                if len(nfts) < 1:
                    print("All nfts retirved")
                    return
                try:
                    t = time.time()
                    self.bulk_insert(r['nfts'], Nft)
                    self._save_next_page(next_page_file, next_pages)
                    saved_pages += len(next_pages)
                except Exception as e:
                    raise e
                if '' in next_pages or None in next_pages:
                    break
                next_page = next_pages[-1]
    
    def insert_nft_events_history(self, collection_slug: str):
        # next_page_file = f'../next_page/opensea/nft_events/{collection_slug}.txt'
        with Session(self.engine) as session:
            after_date = session.execute(select(Collection.created_date).where(Collection.opensea_slug == collection_slug)).scalars().first()
        
        tot_events = 0
        while True:
            first_event = session.execute(select(NftEvent.event_timestamp).where(NftEvent.collection_slug == collection_slug)\
                                        .order_by(NftEvent.event_timestamp).limit(1)).scalars().first()
            if first_event:
                before_date = first_event
            else:
                before_date = None
            events = self.mapper.get_nft_events_for_collection(collection_slug, after_date = after_date, max_recs = 100, before_date = before_date)
            if events:
                t = time.time()
                self.bulk_insert(events, NftEvent)
                tot_events += len(events)
                print(f"Events inserted {tot_events}. Time taken{time.time() - t}")
            else:
                break


    def insert_nft_events(self, collection_slug: str):
        with Session(self.engine) as session:
            last_event = session.execute(select(NftEvent).where(NftEvent.collection_slug == collection_slug)\
                                        .order_by(NftEvent.event_timestamp.desc()).limit(1)).scalars().first()
        if last_event is None:
            print("no event for this collection found in db. retreving hstory")
            self.insert_nft_events_history(collection_slug)
        else:
            after_date = last_event.event_timestamp
            events = self.mapper.get_nft_events_for_collection(collection_slug, after_date = after_date, max_recs = 10000)
            try:
                self.bulk_insert(events, NftEvent)
            except Exception as e:
                print("unable to insert")
            
        

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--slug', help = 'opensea slug of the collection', required = True)
    args = parser.parse_args().__dict__
    # injector = Injector(username='tsdbadmin', password='m9u74pu73bg9fdxi', host='v4ob0qdj5t.y1jft9lh0x.tsdb.cloud.timescale.com', port='35641', database='tsdb')
    injector = Injector()
    
    injector.raw_sql('./app/db/raw_sql/drop_tables.sql')
    injector.raw_sql('./app/db/raw_sql/tables.sql')
    injector.raw_sql('./app/db/raw_sql/hypertables.sql')
    injector.raw_sql('./app/db/raw_sql/indexes.sql')
    # injector.raw_sql('./app/db/raw_sql/compressions.sql')
    # initialize_db()
    injector.insert_collection(args['slug'])
    injector.insert_nfts(args['slug'], num_pages=3)
    injector.insert_nft_events(args['slug'])

if __name__ == "__main__":
    main()