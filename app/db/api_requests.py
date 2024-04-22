import requests
import json
import os
from pprint import pprint
import argparse
import time
from datetime import datetime, date, timedelta
# from utils import append_data_to_file

class OpenSea:
    # class to consume the open sea API
    def __init__(self, chain: str = None):
        # :params chain: chain to search for. Default = None for searching all chains
        self.base_url = "https://api.opensea.io/api/v2/"
        self.headers = {
            "accept": 'application/json',
            'x-api-key': '3765f94c330b42f4a20c2a7310f0d5da'
        }
        self.chain = chain
    
    # def _save_next_page(self, file_path: str, next_page_link: str):
    #     """ utility to save the next page link from previous response. To start from the new page every time. Reduces number of requests made.
    #     :param file_path: path of the file to save the next page link
    #     :param next_page_link: link to te next page
    #     """

    #     with open(file_path, 'a') as f:
    #         f.write(next_page_link)
    #         f.write('\n')
    
    # def get_collections(self, num_req: int = None, perPage: int = 100) -> None:
    #     """ Saves the collection slugs as a list in a json file
    #     :param num_req: restricts the number of requests made, For testing purposes only.
    #     :param perPage: number of collections to retrive per request. Default = 100
    #     """
    #     assert(perPage >= 1 and perPage <= 100), "Number of results per page must be between 1 and 100"
    #     i = 0
    #     next_page_file = '../next_page/collections.txt'
    #     url = self.base_url + 'collections'
    #     params = {}
    #     if self.chain:
    #         params['chain'] = self.chain
    #     params['limit'] = perPage
    #     try:
    #         with open(next_page_file) as f:
    #             params['next'] = f.readlines()[-1]
    #             print(params['next'])
    #             print(params['next'])
    #             print(params['next'])
    #             print(params['next'])
    #             print(params['next'])
    #     except:
    #         pass
    #     r = requests.get(url, headers = self.headers, params = params).json()
    #     collection_slugs = [collection['collection'] for collection in r['collections']]
    #     params['next'] = r['next']
    #     # print(params['next'])
    #     self._save_next_page(next_page_file, params['next'])
    #     i += 1
    #     while params['next'] and i is not num_req:
    #         # time.sleep(0.1)
    #         r = requests.get(url, headers = self.headers, params = params).json()
    #         self._save_next_page(next_page_file, params['next'])
    #         params = r['next']
    #         i += 1
    #         print(f"At page {i}")
        
    #     print(f"Total pages: {i}")
    
    def get_collection(self, collection_slug) -> dict:
        """
        saves the collection metdata for a single colection
        :param collection_slug: uniques opensea identifier of the collection to save
        :param output_file_path: path of the file contiaining the collection metadata
        """
        assert(isinstance(collection_slug, str) and collection_slug), "Please specify a collection slug"
        url = self.base_url + f'collections/{collection_slug}'
        r = requests.get(url, headers = self.headers).json()
        # time.sleep(0.1)
        return r
    
    # def save_collections(self, num_req: int = None, perPage: int = 100):
    #     """
    #     Saves the collection metadata from opnesea in the output file path
    #     :param collection_slug_file: a json file containing the list of collection slugs to get the metadata of
    #     :param output_file_path: path of the file to save te collectio data to. Should be json.
    #     """
    #     # if not os.path.exists(collection_slug_file):
    #     #     self.get_collections(num_req = num_req, perPage = perPage, output_file_path = collection_slug_file)
        
    #     # with open(collection_slug_file, 'r') as f:
    #     #     slugs = json.loads(f.read())
    #     slugs = self.get_collections_from_contracts()
    #     n = len(slugs)
    #     collections = []
    #     for i in range(n):
    #         if i is num_req:
    #             break
    #         collections.append(self.get_collection(slugs[i]))
    #         print(f"Saved collection {i}: {slugs[i]}")
    #     print(f"Saved collection data. Total collections {n}")
    #     return collections
    
    def get_nfts_for_collection(self, collection_slug: str, num_pages: int, perPage: int = 200, next_page: str = None) -> dict:
        """
        saves the nfts for the given collection in specified file path
        :param collection_slug: unique identifier for the collection on opnesea
        :param perPage: limit of NFTs to retireve per request. Limit parameter in the API. Maximum 200
        :param num_req: number of pages to retrieve. Only for testing purposes
        :param next_page: None for json save otherwise sql files
        """
        assert(perPage >= 1 and perPage <= 200), "Number of results returned per page should be between 1 and 200"
        assert(num_pages >= 1), "Number of pages should be at least one"
        url = self.base_url + f'collection/{collection_slug}/nfts'
        i = 0
        nfts = []
        next_pages = []
        params = {}
        params['limit'] = perPage
        # time.sleep(0.1)
        if next_page:
            params['next'] = next_page
        r: dict = requests.get(url, params = params, headers = self.headers).json()
        if r.get('nfts'):
            nfts.extend(r.get('nfts'))
        if r.get('next'):
            params['next'] = r['next']
            next_pages.append(r.get('next'))
        else:
            return {
                'nfts': nfts,
                'next_pages': next_pages
            }
        i += 1
        while params['next']:
            # time.sleep(0.1)
            if i >= num_pages:
                break
            r: dict = requests.get(url, params = params, headers = self.headers).json()
            nfts.extend(r['nfts'])
            params['next'] = r.get('next')
            next_pages.append(params['next'])
            i += 1
            print(f"At page {i}")
        print(f"Retrieved nfts for {collection_slug}. Total {i} pages")
        return {
            'nfts': nfts,
            'next_pages': next_pages
        }
        
    
    def get_collections_from_contracts(self, contract_file = '../data/initial_top_10_games_contracts.txt'):
        """
        Saves the collection slugs for the given smart contracts into a json file. Appends into the existing file
        :param contract_file: the file containing the list of contracts. Must be a text file with one contract address on each line
        :param output_fie: the path for the file to save the collection slugs
        """
        with open(contract_file) as f:
            contracts = f.readlines()
        contracts = [c.strip('\n') for c in contracts]
        url = self.base_url + '/chain/ethereum' + '/contract/{0}'
        collections = set()
        # pprint(contracts)
        for address in contracts:
            # pprint(url.format(address))
            # time.sleep(0.1)
            collection = requests.get(url.format(address), headers = self.headers).json()['collection']
            collections.add(collection)
        print(f"collections requested")
        return list(collections)
    
    def _filter_event(self, event: dict, collection_slug: str):
        if event['event_type'] == 'order':
            return event['asset']['collection'] == collection_slug
        else:
            return event['nft']['collection'] == collection_slug
    
    def get_events_for_collection(self, collection_slug: str, after_date: datetime, before_date: datetime, event_type: str = None, max_recs: int = 1000) -> list:
        # assert(isinstance(event_type, str)), "Event type must be str"
        url = self.base_url + f'events/collection/{collection_slug}'
        i = 0
        params = {}
        events = []
        params['after'] = int(after_date.timestamp())
        if before_date:
            params['before'] = int(before_date.timestamp())
        if event_type:
            params['event_type'] = [event_type]
        else:
            params['event_type'] = ['sale', 'listing', 'transfer']
        t = time.time()
        r = requests.get(url, params = params, headers = self.headers).json()
        # pprint(r)
        e = r.get('asset_events')
        if e:
            events.extend(e)
        else:
            return []
        params['next'] = r.get('next')
        i += 1
        print(f'retieived page {i}')
        while params['next'] and len(events) < max_recs:
            r = requests.get(url, headers = self.headers, params = params).json()
            e = r.get('asset_events')
            if e:
                e = [i for i in e if self._filter_event(i, collection_slug)]
                events.extend(e)
            else:
                break
            params['next'] = r.get('next')
            i += 1
            print(f'retieived page {i}')
        
        print(f'Total events retrieved: {len(events)} in time: {time.time() - t}')
        return events
    
    # def _extract_offer_from_listing(self, listing):
    #     assert(isinstance(listing, dict))
    #     price_info = listing['price']['current']
    #     p = listing['protocol_data']['parameters']
    #     if len(p['offer']) > 1 or p['offer'][0]['item_tye'] in [1, 4, 5]:
    #         return None
    #     else:
    #         item_info = {}
    #         item_info['offerer'] = p['offerer']
    #         item_info['contract'] = p['token']
    #         item_info['token_id'] = p['identifierOrCriteria']
    #         item_info['price'] = price_info['value'] / 10**price_info['decimals']
    #         item_info['currency'] = price_info['currency']
    #         return item_info
    
    # def get_events_for_collection(self, collection_slug: str, after_date: datetime):
    #     url = self.base_url + f'listings/collection/{collection_slug}/all'
    #     if page == 0:
    #         r = requests.get(url, headers = self.headers).json()
    #     else:
    #         try:
    #             with open(next_page_file, 'r') as f:
    #                 next_page = f.readlines()[page - 1]
    #         except:
    #             pass
    #         params = {
    #             'next': next_page
    #         }
    #         r = requests.get(url, headers = self.headers, params = params)
    #     listings = r['listings']
    #     next_page = r['next']
    #     self._save_next_page(next_page_file, next_page)
    #     nft_listings = [self._extract_offer_from_listing(l) for l in listings]
    #     nft_listings = [i for i in nft_listings if i is not None]
    #     while(next_page):
    #         # time.sleep(0.1)
    #         r = requests.get(url, headers = self.headers, params = params)
    #         listings = r['listings']
    #         next_page = r['next']
    #         self._save_next_page(next_page_file, next_page)
    #         nft_listings.extend([self._extract_offer_from_listing(l) for l in listings])
    #         nft_listings = [i for i in nft_listings if i is not None]
        
    #     return nft_listings
    
    # def get_events_by_nft(self, token_id: str, contract_address: str, timeframe: int = 90, event_type: list = ["sale"]):
    #     assert(not token_id == "" and not contract_address == ""), "Please provide token_id or contract addresses"
    #     url = self.base_url + f'events/chain/{self.chain}/contract/{contract_address}/nfts/{token_id}'
    #     after_time_stamp = time.mktime((date.today() - timedelta(days = timeframe)).timetuple())
    #     params = {
    #         'after': after_time_stamp,
    #         'event_type': event_type
    #     }
    #     events = []
    #     while True:
    #         # time.sleep(0.1)
    #         r = requests.get(url, headers = self.headers, params = params).json()
    #         events.extend(r['asset_events'])
    #         if not r['next']:
    #             break

class EtherScan:
    def __init__(self, api_key: str = None):

        self.api_key = 'WZISBUWNRXARTA4MNB4YWRUITQX9XTWRAN'
        self.base_url = 'https://api.etherscan.io/api'
        self.headers = {
            'accept': 'application/json',
        }
    
    def get_block_from_timestamp(self, timestamp: int):
        params = {
            'module': 'block',
            'timestamp': str(timestamp),
            'action': 'getblocknobytime',
            'closest': 'before',
            'apiKey': self.api_key
        }

        r = requests.get(self.base_url, params = params).json()
        return r['result']
    
    def get_erc20_transfers(self, contract_address: str, after_date: datetime):
        assert(isinstance(contract_address, str))
        block_num = self.get_block_from_timestamp(int(after_date.timestamp()))
        params = {
            'action': 'tokentx',
            'module': 'account',
            'contractaddress': contract_address,
            'sort': 'asc',
            'apikey': self.api_key,
            'startblock': str(block_num)
        }

        r = requests.get(self.base_url, headers = self.headers, params = params).json()
        return r['result']

class Alchemy:
    def __init__(self, api_key: str = 'A2_NdhaMRvpVwyotoG4wueAjfgUMGHL1'):
        self.api_key = api_key
        self.base_url = 'https://{chain}.g.alchemy.com/v2/{api_key}'
        self.headers = {
            'accept': 'application/json'
        }
        self.supported_chains = ['eth-mainnet', 'polygon-mainnet', 'arb-mainnet', 'starknet-mainnet', 'opt-mainnet']
        self.ethscan = EtherScan()
    
    def get_nft_sales(self, contract_address: str, from_block: int = 0, next_page: str | None = None, chain: str = 'eth-mainnet', per_page: int = 1000):
        assert chain in self.supported_chains, "Chain not supported. Valid options: eth-mainnet, polygon-mainnet, arb-mainnet, starknet-mainnet, opt-mainnet"
        url = self.base_url.format(chain = chain) + 'getNFTSales'
        params = {
            'contractAddress': contract_address,
            'taker': 'BUYER',
            'fromBlock': from_block,
            'order': 'asc',
        }
        if next_page:
            params['pageKey'] = next_page
        r = requests.get(url, headers = self.headers, params = params).json()
        return {
            'sales': r['nftSales'],
            'next_page': r['pageKey']
        }
    
    def get_nft_transfers(self, contract_address: str, from_block: int = 0, per_page: int = 1000, chain: str = 'eth-mainmet', next_page: str | None = None):
        assert chain in self.supported_chains, "Chain not supported. Valid options: eth-mainnet, polygon-mainnet, arb-mainnet, starknet-mainnet, opt-mainnet"
        max_count = hex(per_page)
        from_block = hex(from_block)
        category = ['erc721', 'erc1155', 'specialnft']
        url = self.base_url.format(chain = chain)
        payload = {
            'id': 1,
            'jsonrpc': '2.0',
            'method': 'alchemy_getAssetTransfers',
            'params': [
                {
                    'fromBlock': from_block,
                    'toBlock': 'latest',
                    'contractAddress': [contract_address],
                    'category': category,
                    'withMetadata': True,
                    'excludeZeroValue': True,
                    'maxCount': max_count
                }
            ]
        }
        if next_page:
            payload['params'][0]['pageKey'] = next_page
        r = requests.post(url, headers = self.headers, json = payload).json()
        return {
            'transfers': r['results']['transfers'],
            'next_page': r['results']['pageKey']
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chain', help = "Chain to restrict the results to", default = None)
    parser.add_argument('--limit_c', help = "limit for collections endpoint", default = 100)
    parser.add_argument('--limit_n', help = "limit for nfts endpoint", default = 200)
    parser.add_argument('--test_n', help = "number of requests for testsing", default = 2)

    args = parser.parse_args().__dict__
    # consumer = OpenSea(args['chain'])
    # consumer.save_collections(perPage = args['limit_c'], num_req = int(args['test_n']))
    # pprint(consumer.get_collection('the-sandbox-assets'))
    # print(consumer.get_collections_from_contracts())
    # consumer.save_collections()
    # pprint(consumer.get_nfts_for_collection(collection_slug='the-sandbox-assets', num_pages=10)['nfts'][30:35])
    # pprint(consumer.get_events_by_collection(collection_slug='the-sandbox-assets', after_date = datetime(2024, 1, 1, 0, 0, 0))[30:35])
    ethscan = EtherScan()
    t = time.time()
    # e = ethscan.get_erc20_transfers('0xBB0E17EF65F82Ab018d8EDd776e8DD940327B28b', page_num=2)
    # pprint(e[30])
    # pprint(f'--------------------------------{len(e)}----------------------------')
    # e = ethscan.get_erc20_transfers('0xBB0E17EF65F82Ab018d8EDd776e8DD940327B28b', page_num=1)
    # pprint(e[30])
    # pprint(f'--------------------------------{len(e)}----------------------------')
    alchemy = Alchemy()
    txs = alchemy.get_nft_transfers('0xa342f5d851e866e18ff98f351f2c6637f4478db5', from_block = 0, per_page = 1000, chain = 'eth-mainnet')
    sales = alchemy.get_nft_sales('0xa342f5d851e866e18ff98f351f2c6637f4478db5', from_block = 0, per_page = 1000, chain = 'eth-mainnet')
    print('-'*50)
    print(f'NFT sales: {len(sales['sales'])}')
    print(f'NFT transfers: {len(txs['transfers'])}')
    pprint('sale:', sales['sales'][0])
    pprint('transfer:', txs['transfers'][0])
    print('-'*50)
    print(f'time: {time.time() - t}')

if __name__ == "__main__":
    main()