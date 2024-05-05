import requests
import json
import os
from pprint import pprint
import argparse
import time
from datetime import datetime, date, timedelta
# from utils import append_data_to_file

class Alchemy:
    def __init__(self):
        self.api_key = os.environ.get('ALCHEMY_API_KEY')
        self.base_url = 'https://{chain}.g.alchemy.com/'
        self.headers = {
            'accept': 'application/json'
        }
        self.supported_chains = ['eth-mainnet', 'polygon-mainnet', 'arb-mainnet', 'starknet-mainnet', 'opt-mainnet']
        self.ethscan = EtherScan()
    
    def get_nft_sales(self, contract_address: str, from_block: int = 0, next_page: str | None = None, chain: str = 'eth-mainnet', per_page: int = 1000):
        assert chain in self.supported_chains, "Chain not supported. Valid options: eth-mainnet, polygon-mainnet, arb-mainnet, starknet-mainnet, opt-mainnet"
        url = self.base_url.format(chain = chain) + f'nft/v3/{self.api_key}/getNFTSales'
        # url = 'https://eth-mainnet.g.alchemy.com/nft/v3/A2_NdhaMRvpVwyotoG4wueAjfgUMGHL1/getNFTSales?fromBlock=0&toBlock=latest&order=asc&contractAddress=0xa342f5d851e866e18ff98f351f2c6637f4478db5&taker=BUYER'
        params = {
            'contractAddress': contract_address,
            'taker': 'BUYER',
            'fromBlock': from_block,
            'order': 'asc',
            'limit': per_page
        }
        # print('-'*50)
        # print('params')
        # pprint(params)
        # print('-'*50)
        if next_page:
            params['pageKey'] = next_page
        r = requests.get(url, headers = self.headers, params = params).json()
        # pprint(r)
        return {
            'sales': r['nftSales'],
            'next_page': r['pageKey']
        }
    
    def get_nft_transfers(self, contract_address: str, from_block: int = 0, per_page: int = 1000, chain: str = 'eth-mainmet', next_page: str | None = None):
        assert chain in self.supported_chains, "Chain not supported. Valid options: eth-mainnet, polygon-mainnet, arb-mainnet, starknet-mainnet, opt-mainnet"
        max_count = hex(per_page)
        from_block = hex(from_block)
        category = ['erc721', 'erc1155', 'specialnft']
        url = self.base_url.format(chain = chain) + f'v2/{self.api_key}'
        payload = {
            'id': 1,
            'jsonrpc': '2.0',
            'method': 'alchemy_getAssetTransfers',
            'params': [
                {
                    'fromBlock': from_block,
                    'toBlock': 'latest',
                    'contractAddresses': [contract_address],
                    'category': category,
                    'withMetadata': True,
                    'excludeZeroValue': True,
                    'maxCount': max_count
                }
            ]
        }
        # print('-'*50)
        # print('params')
        # pprint(payload)
        # print('-'*50)
        if next_page:
            payload['params'][0]['pageKey'] = next_page
        r = requests.post(url, headers = self.headers, json = payload).json()
        return {
            'transfers': r['result']['transfers'],
            'next_page': r['result']['pageKey']
        }
    
    def timestamp_from_block(self, block_num: int, chain: str = 'eth-mainnet'):
        assert chain in self.supported_chains, "Chain not supported. Valid options: eth-mainnet, polygon-mainnet, arb-mainnet, starknet-mainnet, opt-mainnet"
        url = self.base_url.format(chain = chain) + f'v2/{self.api_key}'
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "eth_getBlockByNumber",
            "params": [hex(block_num), False]
        }
        r = requests.post(url, headers = self.headers, json = payload).json()
        # pprint(r)
        return int(r['result']['timestamp'], 16)
