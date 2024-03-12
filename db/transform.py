from datetime import datetime, timedelta
from api_requests import OpenSea, EtherScan
from pprint import pprint

class Mapper:
    def __init__(self, eth_api_key: str = None, alchemy_api_key: str = None):
        self.opensea = OpenSea()
        self.ethscan = EtherScan(eth_api_key)
    
    
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
            'created_date': collection_data['created_date']
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
    
    def get_collection(self, collection_slug: str):
        collection_data = self.opensea.get_collection(collection_slug)
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
    
    def get_nft_events_for_collection(self, collection_slug: str, after_date: datetime, event_type: str = None, max_recs: int = 1000, ):
        events = self.opensea.get_events_for_collection(collection_slug, after_date, event_type = event_type, max_recs = max_recs)
        return [self.map_opensea_nft_event(i) for i in events]
    
    def get_erc20_transfers(self, contract_address: str, after_date: datetime, collection_slug: str):
        transfers = self.ethscan.get_erc20_transfers(contract_address, after_date)
        return [self.map_etherscan_erc20_transfer(i, collection_slug) for i in transfers]

def main():
    collection_slug = 'the-sandbox-assets'
    mapper = Mapper()
    pprint(mapper.get_collection(collection_slug))
    nfts = mapper.get_nfts_for_collection(collection_slug, 2)
    e = mapper.get_nft_events_for_collection(collection_slug, datetime.now() - timedelta(days = 10), event_type = 'sale', max_recs = 300)
    t = mapper.get_erc20_transfers(contract_address = '0x3845badAde8e6dFF049820680d1F14bD3903a5d0', after_date = datetime.now() - timedelta(days = 1), collection_slug = collection_slug)
    pprint(len(nfts['nfts']))
    pprint(nfts['next_pages'])
    pprint(len(e))
    pprint(e[0])
    pprint(len(t))
    pprint(t[0])

if __name__ == "__main__":
    main()