import requests
import json
import os
from pprint import pprint
import argparse
from utils import append_data_to_file

class OpenSea:
    def __init__(self, chain: str = None):
        self.base_url = "https://api.opensea.io/api/v2/"
        self.headers = {
            "accept": 'application/json',
            'x-api-key': 'api-key'
        }
        self.chain = chain
    
    def _save_next_page(self, file_path: str, next_page_link: str):
        with open(file_path, 'w+') as f:
            f.write(next_page_link)
            f.write('\n')
    
    def get_collections(self, num_req: int = None, perPage: int = 100, output_file_path: str = "./data/opensea_collection_slugs.json") -> None:
        assert(perPage >= 1 and perPage <= 100), "Number of results per page must be between 1 and 100"
        i = 0
        next_page_file = './next_page/collections.txt'
        url = self.base_url + 'collections'
        params = {}
        if self.chain:
            params['chain'] = self.chain
        params['limit'] = perPage
        if os.exists(next_page_file):
            with open(next_page_file) as f:
                params['next'] = f.readlines()[-1]
        r = requests(url, headers = self.headers).json()
        # with open(output_file_path, 'w') as f:
            # append_data_to_file()
        collection_slugs = [collection['collection'] for collection in r['collections']]
        append_data_to_file(file_path = output_file_path, new_data = collection_slugs)
        params['next'] = r['next']
        self._save_next_page(next_page_file, params['next'])
        i += 1
        while params['next']:
            r = requests(url, headers = self.headers, params = self.params).json()
            append_data_to_file(file_path = output_file_path, new_data = collection_slugs)
            self._save_next_page(next_page_file, params['next'])
            params = r['next']
            i += 1
            print(f"Saved page {i}")
            if i == num_req:
                break
        
        print(f"Total pages saved: {i}")
    
    def get_collection(self, collection_slug, output_file_path: str = "./data/opensea_collections.json"):
        assert(isinstance(collection_slug, str) and collection_slug), "Please specify a collection slug"
        url = self.base_url + f'collection/{collection_slug}'
        r = requests.get(url).json()
        append_data_to_file(output_file_path, r)
        return r
    
    def save_collections(self, collection_slug_file: str = "./data/opensea_collection_slugs.json", output_file_path: str = "./data/opensea_collections.json", num_req: int = None):
        try:
            with open(collection_slug_file, 'r') as f:
                slugs = json.loads(f.read())
            n = len(slugs)
            for i in range(n):
                self.get_collection(slugs[i], output_file_path = output_file_path)
                print(f"Saved collection {i}: {slugs[i]}")
                if i == num_req:
                    break
            print(f"Saved collection data. Total collections {n}")
        except:
            print("Invalid file path")
    
    def save_nfts_for_collection(self, collection_slug: str, perPage: int = 200, num_req: int = 2):
        assert(perPage >= 1 and perPage <= 200), "Number of results returned per page should be between 1 and 200"
        url = self.base_url + f'collection/{collection_slug}/nfts'
        i = 0
        output_file_path = f'./data/{collection_slug}_nfts.json'
        next_page_file = f'./next_page/{collection_slug}'
        params = {}
        try:
            with open(next_page_file, 'r') as f:
                params['next'] = f.readlines()[-1]
        except:
            pass
        params['limit'] = perPage
        r = requests.get(url, params = params).json()
        append_data_to_file(output_file_path, r['nfts'])
        params['next'] = r['next']
        self._save_next_page(next_page_file, params['next'])
        i += 1
        while params['next']:
            r = requests.get(url).json()
            append_data_to_file(output_file_path, r['nfts'])
            params['next'] = r['next']
            self._save_next_page(next_page_file, params['next'])
            i += 1
            if i == num_req:
                break
            print(f"Saved page {i}")
        
        print(f"Saved nfts for {collection_slug}. Total {i} pages")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chain', help = "Chain to restrict the results to", default = "ethereum")
    parser.add_argument('--limit_c', help = "limit for collections endpoint", default = 100)
    parser.add_argument('--limit_n', help = "limit for nfts endpoint", default = 200)
    parser.add_argument('--test_n', help = "number of requests for testsing", default = 2)

    args = parser.parse_args().__dict__
    consumer = OpenSea(args['chain'])
    consumer.save_collections(perPage=args['limit_c'])
    consumer.save_nfts_for_collection(perPage=args['limit_n'], collection_slug='gods-unchained')