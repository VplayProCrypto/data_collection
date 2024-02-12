import requests
import os
import json
import argparse
from pprint import pprint
from utils import append_data_to_file

class Alchemy:
    def __init__(self, chain: str = "eth-mainnet"):
        self.chain = chain
        self.headers = {
            'accept': 'application/json'
        }
        self.api_key = ''
        self.base_url = f'https://eth-mainnet.g.alchemy.com/nft/v3/{self.api_key}/'
    
    def get_contract_data(self, contract_address: str, output_file_path = './data/contracts.json'):
        assert(isinstance(contract_address, str) and contract_address), "Please enter a contract address"
        url = self.base_url + 'getContractMetadata'
        params = {
            'contract': contract_address
        }
        r = requests.get(url, headers = self.headers, params = params).json()