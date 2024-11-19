import psycopg2
import argparse
import time
import json
import asyncio
import logging
import requests
import aiohttp
from typing import List, Set
from datetime import datetime, timezone
from asyncio import Semaphore
# from sqlmodel import Session as S
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text, func, create_engine, inspect, select
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

import app.keys as keys
from app.orm.transform import Mapper
from app.logging_config import setup_logging
from app.api_requests.etherscan import EtherScan
from app.orm.rr import calculate_nft_roi, calculate_and_store_collection_roi
from .models import Collection, CollectionDynamic, Contract, NFT, NFTEvent, \
    NftOwnership, ERC20Transfer, PaymentToken, TokenPrice, Fee, NFTDynamic


class Injector:
    def __init__(self, username: str = None, password: str = None, port: str = None, database: str = None, host: str = None, eth_api_key: str = None, alchemy_api_key: str = None):
        # setup_logging()
        self.logger = logging.getLogger(__name__)
        # self.username = 'tsdbadmin'
        # self.port = '32026'
        # self.database = 'tsdb'
        # self.password = 'km8en9w8a96ghdtl'
        # self.host = 'busvxhxzr1.b505mpo6st.tsdb.cloud.timescale.com'
        # if not username:
        #     self.url = f'postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}'
        # else:
        #     self.url = f'postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}'
        self.engine = create_engine(keys.timescale_url)
        self.async_engine = create_async_engine(
            keys.timescale_url_async,
            pool_size = 10
        )
        self.mapper = Mapper(eth_api_key = eth_api_key, alchemy_api_key = alchemy_api_key)
        with open('app/games.json') as f:
            self.games = json.loads(f.read())
    
    def close(self):
        self.engine.dispose()
        self.mapper.close_sessions()
    
    # def __del__(self):
    #     del self.mapper

    
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
        # print('----------------------')
        # print([i for i in new_data if i['event_timestamp'] is None][:5])
        # print(new_data[:5])
        # print('----------------------')
        index_columns = [key.name for key in inspect(model).primary_key]
        if upsert:
            # self.logger.info(index_columns)
            smt = insert_smt.on_conflict_do_update(index_elements=index_columns, set_=insert_smt.excluded)
        else:
            smt = insert_smt.on_conflict_do_nothing(index_elements = index_columns)
        return smt


    def bulk_insert(self, new_data: List[dict], model, upsert: bool = False):
        t = time.time()
        if len(new_data) < 1:
            return
        with Session(self.engine) as session:
            # with session.begin():
                try:
                    session.execute(self.get_insert_smt(new_data, model, upsert))
                    session.commit()
                    self.logger.info(f'Time Taken to insert: {time.time() - t}')
                    # print(f'Time Taken to insert: {time.time() - t}')
                except ProgrammingError as e:
                    if isinstance(e.orig, psycopg2.errors.InFailedSqlTransaction):
                        # Rollback the session to exit the aborted state
                        session.rollback()
                        index_columns = [key.name for key in inspect(model).primary_key]
                        without_duplicates = self._remove_duplicates(new_data, index_columns)
                        session.execute(self.get_insert_smt(without_duplicates, model, upsert))
                        # session.commit()
                        self.logger.info(f'Time Taken to insert: {time.time() - t}')
                    else:
                        raise e
                except SQLAlchemyError as e:
                    # This catches other SQLAlchemy-related errors
                    session.rollback()  # Ensure the session is rolled back on any error
                    self.logger.error(f"SQLAlchemy error occurred: {e}")
                    raise e
    
    def insert_collection(self, collection_slug: str):
        self.logger.info(f'Adding Collection: {collection_slug}')
        data = self.mapper.get_collection(collection_slug)
        # self.logger.info(data.keys())
        collection = Collection(**data['collection'])
        # self.logger.info(collection)
        for i in data['fees']:
            collection.fees.append(Fee(**i))
        # self.logger.info(collection.fees)
        for i in data['contracts']:
            collection.contracts.append(Contract(**i))
        # self.logger.info(collection.contracts)
        try:
            with Session(self.engine) as session:
                # with session.begin():
                    session.merge(collection)
                    session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e
    
    def insert_nfts(self, collection_slug: str, num_pages: int = None):
        next_page_file = f'app/next_page/opensea/nft/{collection_slug}.txt'
        try:
            with open(next_page_file, 'r') as f:
                next_page = f.readlines()[-1]
                self.logger.info(f'NFT: Collection: {collection_slug}, page: {next_page}')
        except FileNotFoundError or FileExistsError or IndexError as e:
            next_page = None
        
        if num_pages:
            self.logger.info(f'NFT: Collection: {collection_slug}, page: {next_page}')
            r = self.mapper.get_nfts_for_collection(collection_slug, num_pages = num_pages, next_page = next_page)
            nfts = r['nfts']
            next_pages = r['next_pages']
            if len(nfts) < 1:
                self.logger.info("All nfts retirved")
                return
            try:
                t = time.time()
                self.bulk_insert(nfts, NFT)
                self._save_next_page(next_page_file, next_pages)
                self.logger.info(f"saved pages {len(nfts)}. Time taken: {time.time() - t} seconds")
            except Exception as e:
                raise e
        else:
            saved_pages: int = 0
            while True:
                self.logger.info(f'NFT: Collection: {collection_slug}, page: {next_page}')
                r = self.mapper.get_nfts_for_collection(collection_slug, num_pages = 1, next_page = next_page)
                nfts = r['nfts']
                # self.logger.info(nfts[:2])
                next_pages = r['next_pages']
                if len(nfts) < 1 or not next_pages:
                    self.logger.info("All nfts retirved")
                    return
                try:
                    self.bulk_insert(r['nfts'], NFT)
                    self._save_next_page(next_page_file, next_pages)
                    saved_pages += len(next_pages)
                except Exception as e:
                    raise e
                if not next_pages or '' in next_pages or None in next_pages:
                    break
                next_page = next_pages[-1]
    
    # def insert_nft_events_history(self, collection_slug: str):
    #     # next_page_file = f'../next_page/opensea/nft_events/{collection_slug}.txt'
    #     with Session(self.engine) as session:
    #         after_date = session.execute(select(Collection.created_date).where(Collection.opensea_slug == collection_slug)).scalars().first()
        
    #     tot_events = 0
    #     while True:
    #         first_event = session.execute(select(NFTEvent.event_timestamp).where(NFTEvent.collection_slug == collection_slug)\
    #                                     .order_by(NFTEvent.event_timestamp).limit(1)).scalars().first()
    #         if first_event:
    #             before_date = first_event
    #         else:
    #             before_date = None
    #         events = self.mapper.get_nft_events_for_collection(collection_slug, after_date = after_date, max_recs = 100, before_date = before_date)
    #         if events:
    #             # t = time.time()
    #             self.bulk_insert(events, NFTEvent)
    #             tot_events += len(events)
    #             self.logger.info(f"Events inserted {tot_events}")
    #         else:
    #             break
    
    def insert_nft_events_contract(self, collection_slug: str, contract: str, event_type: str = 'transfer'):
        with Session(self.engine) as session:
            # with session.begin():
                last_event = session.execute(
                    select(NFTEvent)
                    .where(NFTEvent.collection_slug == collection_slug)
                    .where(NFTEvent.event_type == event_type)
                    .where(func.lower(NFTEvent.contract_address) == func.lower(contract['contract_address']))
                    .order_by(NFTEvent.event_timestamp.desc()).limit(1))
                last_event = last_event.scalars().first()
        
                if last_event is None:
                    self.logger.info(f"no {event_type} event for {collection_slug} found in db. retreving hstory")
                    # self.insert_nft_events_history(collection_slug)
                    # with Session(self.engine) as session:
                        # after_date = session.execute(select(Collection.created_date).where(Collection.opensea_slug == collection_slug)).scalars().first()
                    from_block = 0
                else:
                    from_block = last_event.block_number
                    self.logger.info(f'retrieving after: {last_event.event_timestamp}')
        next_page = None
        if event_type == 'sale':
            per_page = 100
        else:
            per_page = 1000
        while True:
            res = self.mapper.get_nft_events_for_collection(collection_slug, from_block = from_block, per_page = per_page, next_page=next_page, contract = contract, event_type = event_type)
            # self.logger.info(res['events'][0])
            try:
                self.bulk_insert(res['events'], NFTEvent)
                next_page = res['next_page']
                print(next_page)
                self.logger.info(f'Added: {str(len(res["events"]))}')
            except Exception as e:
                self.logger.error("unable to insert. Skipping entire block")
                self.logger.error(e)
                break
            if not next_page:
                self.logger.info(f'All events retrieved for {collection_slug}:{contract}')
                break

    def insert_nft_events(self, collection_slug: str, event_type: str = 'transfer'):
        self.logger.info(f"Adding {event_type} for {collection_slug}")
        with Session(self.engine) as session:
            # with session.begin():
                raw_collection = session.execute(
                    select(Collection)
                    .where(Collection.opensea_slug == collection_slug)
                    .options(selectinload(Collection.contracts))
                    .limit(1)
                )
                collection: Collection = raw_collection.scalars().first()
                contracts = [i.model_dump() for i in collection.contracts]
        
        self.logger.info(contracts)
        for contract in contracts:
            self.logger.info(f"Contract: {contract}")
            self.insert_nft_events_contract(collection_slug, contract, event_type)
    
    def insert_erc20_transfers(self, collection_slug: str):
        # etherscan = EtherScan()
        # transfers = etherscan.get_erc20_transfers
        game_id = self.mapper._get_game_id(collection_slug)
        for erc_contract in self.games[game_id]['erc20Tokens']:
            self.logger.info(f'inserting contract: {erc_contract}')
            prev_last_record = None
            while True:
                with Session(self.engine) as session:
                    # with session.begin():
                        raw_last_record = session.execute(
                            select(ERC20Transfer)\
                            .where(ERC20Transfer.contract_address == erc_contract.lower())\
                            .order_by(ERC20Transfer.event_timestamp.desc())\
                            .limit(1)
                        )
                        last_record = raw_last_record.scalars().first()
                        if last_record:
                            if prev_last_record == last_record:
                                self.logger.info('All erc20 transfers inserted')
                                break
                            after_date = last_record.event_timestamp
                            prev_last_record = last_record
                        else:
                            self.logger.info(f'no transfers for this erc 20 token: {erc_contract}. Retrieving history')
                            raw_after_date = session.execute(
                                select(Collection.created_date)\
                                .where(Collection.opensea_slug == collection_slug)\
                                .limit(1)
                            )
                            after_date = raw_after_date.scalars().first()
                self.logger.info(f'retreiving after: {after_date}, last record: {last_record or "None"}')
                t = time.time()
                transfers = self.mapper.get_erc20_transfers(erc_contract, after_date, collection_slug)
                self.logger.info(f'Retrival time: {time.time() - t} seconds')
                if len(transfers) == 0:
                    # pself.logger.info()
                    break
                try:
                    self.bulk_insert(transfers, ERC20Transfer, upsert = False)
                    self.logger.info(f'Added transfers: {str(len(transfers))}')
                except Exception as e:
                    self.logger.error('-'*50, 'error', '-'*50)
                    self.logger.error(str(e))
                    break
    
    def calculate_and_store_rr(self, game_id: str):
        with Session(self.engine) as session:
            # # with session.begin():
            nft_rois = calculate_nft_roi(session, game_id, self.games)
            self.bulk_insert(nft_rois, NFTDynamic, upsert = False)
            calculate_and_store_collection_roi(session, game_id, self.mapper)
    
    def _update_nft_status_to_failed(self, contract_address: str, token_id: str):
        with Session(self.engine) as session:
            # with session.begin():
                nft = session.get(NFT, (contract_address.lower(), token_id))
                if nft:
                    nft.status = "failed"
                    session.add(nft)
                    session.commit()


    def retrieve_missing_traits(self, contract_address: str, token_id: str):
        try:
            # Update the status to 'in-progress'
            with Session(self.engine) as session:
                # with session.begin():
                    statement = select(NFT).where(
                        (func.lower(NFT.contract_address) == func.lower(contract_address)) &
                        (NFT.token_id == token_id) &
                        (NFT.status.in_(["new", "failed"]))
                    ).with_for_update()
                    
                    raw_nft = session.execute(statement)
                    nft = raw_nft.scalar_one_or_none()
                    if nft:
                        # nft.status = "in-progress"
                        url = nft.metadata_url
                        # session.add(nft)
                    else:
                        return  # Skip if the NFT is already in progress or completed

            # Fetch the traits from the external API
            traits = self.mapper.get_nft_traits(url)
            # print(traits)

            # Update the traits and set status to 'completed' or 'failed'
            # # with session.begin():
            with Session(self.engine):
                # with session.begin():
                    nft = session.execute(
                        select(NFT)
                        .where(func.lower(NFT.contract_address) == func.lower(contract_address))
                        .where(NFT.token_id == token_id)
                    )
                    nft = nft.scalar_one_or_none()

                    if nft:
                        nft.status = "completed" if traits else "no-traits"
                        nft.traits = traits
                        nft.updated_at = datetime.now(tz=timezone.utc)
                        session.add(nft)
                        self.logger.info(f'Traits fetched for NFT: {contract_address}/{token_id}')
                        session.commit()  # Commit the changes to persist to the database

        except requests.exceptions.RequestException as e:
        # except aiohttp.ClientError as e:
            self.logger.error(f"Failed to retrieve traits for {contract_address}/{token_id}: {e}")
            self._update_nft_status_to_failed(contract_address, token_id)
        except Exception as e:
            self.logger.error(f'Error while retieving traits for NFT: {contract_address}/{token_id}: {e.args}')
            self._update_nft_status_to_failed(contract_address, token_id)

        # except NoResultFound:
        #     self.logger.error(f"NFT not found in database for contract_address={contract_address}, token_id={token_id}")


    # Enqueue the retrieval tasks for all NFTs that are marked 'new' or 'failed'
    def retrieve_missing_traits_all(self, collection_slug: str):
        with Session(self.engine) as session:
            # with session.begin():
                statement = (
                    select(
                        NFT.contract_address,
                        NFT.token_id
                    )
                    .where(NFT.status.in_(["new", "failed"]))
                    .where(NFT.metadata_url.isnot(None))
                    .where(NFT.collection_slug == collection_slug)
                    .order_by(NFT.token_id)
                )
                raw_results = session.execute(statement)
                results = raw_results.all()
                # sem = Semaphore(50)
                # def retrieve_with_limit(nft):
                #     # with sem:
                #         self.retrieve_missing_traits(nft.contract_address, nft.token_id)
                # tasks = [retrieve_with_limit(nft) for nft in results]
                # asyncio.gather(*tasks)
        
        for nft in results:
            self.retrieve_missing_traits(nft.contract_address, nft.token_id)

                # print(nft)

        

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--slug', help = 'opensea slug of the collection', required = True)
    args = parser.parse_args().__dict__
    # injector = Injector(username='tsdbadmin', password='m9u74pu73bg9fdxi', host='v4ob0qdj5t.y1jft9lh0x.tsdb.cloud.timescale.com', port='35641', database='tsdb')
    injector = Injector()
    
    # injector.raw_sql('./app/db/raw_sql/drop_tables.sql')
    # injector.raw_sql('./app/db/raw_sql/tables.sql')
    # injector.raw_sql('./app/db/raw_sql/hypertables.sql')
    # injector.raw_sql('./app/db/raw_sql/indexes.sql')
    # injector.raw_sql('./app/db/raw_sql/triggers.sql')
    # injector.raw_sql('./app/db/raw_sql/compressions.sql')
    # initialize_db()
    injector.insert_collection(args['slug'])
    injector.insert_nfts(args['slug'])
    injector.insert_nft_events(args['slug'], event_type='transfer')
    injector.insert_nft_events(args['slug'], event_type='sale')
    injector.insert_erc20_transfers(args['slug'])
    injector.calculate_and_store_rr(injector.mapper._get_game_id(args['slug']))

if __name__ == "__main__":
    main()