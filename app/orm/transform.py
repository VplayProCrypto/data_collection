import json
import time

from datetime import datetime, timedelta
from pprint import pprint
from copy import deepcopy
from api_requests.alchemy import Alchemy
from api_requests.opensea import OpenSea
from api_requests.etherscan import EtherScan
from utils import unflatten_nested_lists

class Mapper:
    def __init__(self, eth_api_key: str = None, alchemy_api_key: str = None, game_names_file: str = "games.json"):
        self.opensea = OpenSea()
        self.ethscan = EtherScan()
        self.alchemy = Alchemy()
        
        with open(game_names_file) as f:
            self.games = json.loads(f.read())
    
    def __del__(self):
        del self.alchemy
        del self.opensea
        del self.ethscan
    
    def _get_game_name(self, collection_slug: str):
        name = ""
        for i in self.games.keys():
            if i in collection_slug:
                name = self.games[i]['name']
        
        return name
    
    def _get_game_id(self, collection_slug: str):
        for i in self.games.keys():
            if i in collection_slug:
                return i
    
    
    def map_opensea_collection(self, collection_data: dict):
        collection_slug = collection_data['collection']
        game_name = self._get_game_name(collection_slug)
        game_id = self._get_game_id(collection_slug)
        tags = ','.join(self.games[game_id]['tags'])
        # pprint(collection_data)
        return {
            'opensea_slug': collection_data['collection'],
            'name': collection_data['name'],
            'game_name': game_name,
            'game_id': game_id,
            'description': collection_data['description'],
            'owner': collection_data['owner'],
            'category': collection_data['category'],
            'is_nsfw': collection_data['is_nsfw'],
            'tags': tags,
            'entry_fee': self.games[game_id]['entry_fee'],
            'entry_fee_currency': self.games[game_id]['entry_fee_currency'],
            'opensea_url': collection_data['opensea_url'],
            'project_url': collection_data['project_url'],
            'wiki_url': collection_data['wiki_url'],
            'discord_url': collection_data['discord_url'],
            'telegram_url': collection_data['telegram_url'],
            'twitter_url': collection_data['twitter_username'],
            'instagram_url': collection_data['instagram_username'],
            'created_date': datetime.fromisoformat(collection_data['created_date'])
        }
    
    def map_opensea_nft_event(self, event_data: dict):
        assert(isinstance(event_data, dict))
        mapped_event = {
            'transaction_hash': None,
            'token_id': None,
            'contract_address': None,
            'event_timestamp': None,
            'buyer': None,
            'seller': None,
            'price_val': None,
            'quantity': 0,
            'price_currency': None,
            'price_decimals': None,
            'start_date': None,
            'expiration_date': None,
            'event_type': None,
            'collection_slug': None
        }
        mapped_event['event_type'] = event_data['event_type']
        mapped_event['event_timestamp'] = datetime.fromtimestamp(event_data['event_timestamp'])
        mapped_event['quantity'] = event_data['quantity']
        if mapped_event['event_type'] == 'sale':
            mapped_event['transaction_hash'] = event_data['transaction']
            mapped_event['token_id'] = event_data['nft']['identifier']
            mapped_event['contract_address'] = event_data['nft']['contract']
            mapped_event['collection_slug'] = event_data['nft']['collection']
            mapped_event['buyer'] = event_data['buyer']
            mapped_event['seller'] = event_data['seller']
            mapped_event['price_val'] = event_data['payment']['quantity']
            mapped_event['price_symbol'] = event_data['payment']['symbol']
            mapped_event['price_decimals'] = event_data['payment']['decimals']
        elif mapped_event['event_type'] == 'transfer':
            mapped_event['transaction_hash'] = event_data['transaction']
            mapped_event['token_id'] = event_data['nft']['identifier']
            mapped_event['contract_address'] = event_data['nft']['contract']
            mapped_event['collection_slug'] = event_data['nft']['collection']
            mapped_event['buyer'] = event_data['to_address']
            mapped_event['seller'] = event_data['from_address']
        elif mapped_event['event_type'] == 'order':
            mapped_event['event_type'] = 'listing'
            mapped_event['token_id'] = event_data['asset']['identifier']
            mapped_event['contract_address'] = event_data['asset']['contract']
            mapped_event['collection_slug'] = event_data['asset']['collection']
            mapped_event['seller'] = event_data['maker']
            mapped_event['start_date'] = datetime.fromtimestamp(event_data['start_date'])
            t = event_data['expiration_date']
            mapped_event['expiration_date'] = datetime.fromtimestamp(t) if t else None
        
        mapped_event['game_id'] = self._get_game_id(mapped_event['collection_slug'])
        return mapped_event
    
    def map_alchemy_nft_sale(self, sale_data: dict, collection_slug: str, game_id: str):
        # pprint(sale_data)
        mapped_event = {
            'transaction_hash': None,
            'token_id': None,
            'contract_address': None,
            'event_timestamp': None,
            'buyer': None,
            'block_number': None,
            'seller': None,
            'price_val': None,
            'quantity': 0,
            'price_currency': None,
            'price_decimals': None,
            'event_type': None,
            'collection_slug': None,
            'game_id': None,
            'marketplace': None,
            'marketplace_address': None
        }
        mapped_event['event_type'] = 'sale'
        mapped_event['event_timestamp'] = datetime.fromtimestamp(self.alchemy.timestamp_from_block(sale_data['blockNumber']))
        mapped_event['transaction_hash'] = sale_data['transactionHash']
        mapped_event['token_id'] = sale_data['tokenId']
        mapped_event['contract_address'] = sale_data['contractAddress']
        mapped_event['collection_slug'] = collection_slug
        mapped_event['marketplace'] = sale_data['marketplace']
        mapped_event['marketplace_address'] = sale_data['marketplaceAddress']
        mapped_event['game_id'] = game_id
        mapped_event['buyer'] = sale_data['buyerAddress']
        mapped_event['seller'] = sale_data['sellerAddress']
        mapped_event['price_val'] = sale_data['sellerFee']['amount']
        mapped_event['price_currency'] = sale_data['sellerFee']['symbol']
        mapped_event['price_decimals'] = sale_data['sellerFee']['decimals']
        mapped_event['block_number'] = sale_data['blockNumber']
        mapped_event['quantity'] = int(sale_data['quantity'])

        return mapped_event
    
    def map_alchemy_nft_transfer(Self, transfer_data: dict, collection_slug: str, game_id: str):
        mapped_event = {
            'transaction_hash': None,
            'token_id': None,
            'contract_address': None,
            'event_timestamp': None,
            'block_number': None,
            'buyer': None,
            'seller': None,
            'price_val': None,
            'quantity': 0,
            'price_currency': None,
            'price_decimals': None,
            'event_type': None,
            'collection_slug': None,
            'game_id': None,
            'marketplace': None,
            'marketplace_address': None
        }
        mapped_event['event_type'] = 'transfer'
        mapped_event['event_timestamp'] = datetime.fromisoformat(transfer_data['metadata']['blockTimestamp'][:-1])
        mapped_event['buyer'] = transfer_data['to']
        mapped_event['seller'] = transfer_data['from']
        mapped_event['transaction_hash'] = transfer_data['hash']
        mapped_event['block_number'] = int(transfer_data['blockNum'], 16)
        mapped_event['collection_slug'] = collection_slug
        mapped_event['game_id'] = game_id
        mapped_event['contract_address'] = transfer_data['rawContract']['address']
        if transfer_data['category'] == 'erc721':
            mapped_event['token_id'] = str(int(transfer_data['erc721TokenId'], 16))
            mapped_event['quantity'] = 1
            return mapped_event
        elif transfer_data['category'] == 'erc1155':
            mapped_events = []
            nfts = transfer_data['erc1155Metadata']
            for i in nfts:
                mapped_event['token_id'] = str(int(i['tokenId'], 16))
                mapped_event['quantity'] = int(i['value'], 16)
                mapped_events.append(deepcopy(mapped_event))
            return mapped_events
        else:
            raise ValueError(f"Invalid category: {transfer_data['category']}")
    
    def map_opensea_contract(self, contract_data: dict, collection_slug: str):
        return {
            'collection_slug': collection_slug,
            'contract_address': contract_data['address'],
            'chain': contract_data['chain']
        }
    
    def map_etherscan_erc20_transfer(self, transfer_data: dict, collection_slug: str):
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
    
    def map_opensea_fee(self, fee_data: dict, collection_slug: str):
        return {
            'collection_slug': collection_slug,
            'fee': fee_data['fee'],
            'recipient': fee_data['recipient'],
        }
    
    def map_opensea_nft(self, nft_data: dict):
        collection_slug = nft_data['collection']
        game_id = self._get_game_id(collection_slug)
        return {
            'collection_slug': nft_data['collection'],
            'token_id': nft_data['identifier'],
            'game_id': game_id,
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
    
    def map_payment_tokens(self, token_data: dict):
        return {
            'collection_slug': token_data['collection_slug'],
            'contract_address': token_data['contract_address'],
            'symbol': token_data['symbol'],
            'decimals': token_data['decimals'],
            'chain': token_data['chain'],
        }
    
    def map_token_price(self, price_data: dict):
        return {
            'contract_address': price_data[''],
            'eth_price': price_data[''],
            'usdt_price': price_data[''],
            'usdt_conversion_price': price_data[''],
            'eth_conversion_price': price_data[''],
            'event_timestamp': datetime.fromtimestamp(price_data[''])
        }
    
    def map_opensea_collection_stats(self, collection_stats):
        return {
            'num_owners': collection_stats['total']['num_owners'],
            'market_cap': collection_stats['total']['market_cap'],
            'floor_price': collection_stats['total']['floor_price'],
            'floor_price_currency': collection_stats['total']['floor_price_symbol']
        }
    
    def get_collection(self, collection_slug: str):
        collection_data = self.opensea.get_collection(collection_slug)
        # pprint(collection_data)
        collection = self.map_opensea_collection(collection_data)
        fees = [self.map_opensea_fee(i, collection_slug) for i in collection_data['fees']]
        contracts = [self.map_opensea_contract(i, collection_slug) for i in collection_data['contracts']]
        return {
            'collection': collection,
            'fees': fees,
            'contracts': contracts
        }
    
    def get_nfts_for_collection(self, collection_slug: str, num_pages: int = 10, next_page: str = None):
        r = self.opensea.get_nfts_for_collection(collection_slug, num_pages = num_pages, next_page = next_page)
        r['nfts'] = [self.map_opensea_nft(i) for i in r['nfts']]
        return r
    
    def map_chain_to_alchemy_chain(self, chain: str):
        if chain == 'ethereum':
            return 'eth-mainnet'
        elif chain == 'polygon':
            return 'polygon-mainnet'
        elif chain == 'arbitum':
            return 'arb-mainnet'
        # elif chain == 'polygon':
        #     return 'polygon-mainnet'
        # elif chain == 'polygon':
        #     return 'polygon-mainnet'
        # else:
        #     raise ValueError(f"Invalid chain: {chain}")
    
    def get_nft_events_for_collection(self, collection_slug: str, contract: dict, from_block: int, event_type: str = 'transfer', per_page: int = 1000, next_page: str | None = None):
        game_id = self._get_game_id(collection_slug)
        events = []
        # if len(contracts) < 1:
            # print('No contracts present. NFTs')
        # contracts_alc = [i for i in contracts if i['chain'] in ['ethereum', 'polygon', 'arbitum']]
        if contract['chain'] != 'ethereum':
            print(f"Chain not supported: {contract['chain']}")
            return {
                'events': [],
                'next_page': None
            }
        if event_type == 'sale':
            # pprint(ca)
            r = self.alchemy.get_nft_sales(contract['contract_address'], from_block, next_page=next_page, chain = self.map_chain_to_alchemy_chain(contract['chain']), per_page=per_page)
            events = r['sales']
            # print(len(events))
            events_mapped = [self.map_alchemy_nft_sale(i, collection_slug, game_id) for i in events]
            return {
                'events': unflatten_nested_lists(events_mapped),
                'next_page': r['next_page']
            }
        if event_type == 'transfer':
            # print('-------------------------------------------------------------------')
            # print('Adding transfer event')
            # pprint(ca)
            r = self.alchemy.get_nft_transfers(contract['contract_address'], from_block, next_page=next_page, chain = self.map_chain_to_alchemy_chain(contract['chain']), per_page=per_page)
            events = r['transfers']
            events_mapped = [self.map_alchemy_nft_transfer(i, collection_slug, game_id) for i in events]
            # pprint(events_mapped[0])
            # print('-------------------------------------------------------------------')
            return {
                'events': unflatten_nested_lists(events_mapped),
                'next_page': r['next_page']
            }
        raise ValueError(f"Invalid event type: {event_type}")
    
    # def get_nft_events_for_collection(self, collection_slug: str, after_date: datetime, before_date: datetime, event_type: str = None, max_recs: int = 1000):
    #     events = self.opensea.get_events_for_collection(collection_slug, after_date, event_type = event_type, max_recs = max_recs, before_date = before_date)
    #     return [self.map_opensea_nft_event(i) for i in events]
    
    def get_erc20_transfers(self, contract_address: str, after_date: datetime, collection_slug: str):
        transfers = self.ethscan.get_erc20_transfers(contract_address, after_date)
        # print('-'*50)
        # print('inside mapper erc20')
        # pprint(transfers[0])
        # print('-'*50)
        return [self.map_etherscan_erc20_transfer(i, collection_slug) for i in transfers]
    
    def get_collection_stats(self, collection_slug: str):
        stats = self.opensea.get_collection_stats(collection_slug)
        return self.map_opensea_collection_stats(stats)

def main():
    collection_slug = 'the-sandbox-assets'
    mapper = Mapper()
    collection = mapper.get_collection(collection_slug)
    nfts = mapper.get_nfts_for_collection(collection_slug, 2)
    pprint(collection)
    pprint(collection['contracts'])
    # contracts = [mapper.map_opensea_contract(i, collection_slug) for i in collection['contracts']]
    e = mapper.get_nft_events_for_collection(collection_slug, contracts = collection['contracts'],
                                             from_block=0, event_type = 'sale',
                                             max_recs = 100)['events']
    # t = mapper.get_erc20_transfers(contract_address = '0x3845badAde8e6dFF049820680d1F14bD3903a5d0', after_date = datetime.now() - timedelta(days = 1), collection_slug = collection_slug)
    # pprint(len(nfts['nfts']))
    # pprint(nfts['next_pages'])
    pprint(len(e))
    a = [i for i in e if i['quantity'] > 1]
    pprint(a[0])
    pprint(e[1])
    pprint(e[2])
    # pprint(len(t))
    # pprint(t[0])

if __name__ == "__main__":
    main()