import requests
import json
import os
from pprint import pprint
import argparse
import time
from datetime import datetime, date, timedelta
# from utils import append_data_to_file


class EtherScan:
    def __init__(self ):

        self.api_key = os.environ.get('ETHERSCAN_API_KEY')
        self.base_url = os.environ.get('ETHERSCAN_BASE_URL')
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
