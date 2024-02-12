import requests
import json
import os
from pprint import pprint
import argparse
from utils import append_data_to_file

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
    
    def _save_next_page(self, file_path: str, next_page_link: str):
        """ utility to save the next page link from previous response. To start from the new page every time. Reduces number of requests made.
        :param file_path: path of the file to save the next page link
        :param next_page_link: link to te next page
        """

        with open(file_path, 'a') as f:
            f.write(next_page_link)
            f.write('\n')
    
    def get_collections(self, num_req: int = None, perPage: int = 100, output_file_path: str = "./data/opensea_collection_slugs.json") -> None:
        """ Saves the collection slugs as a list in a json file
        :param num_req: restricts the number of requests made, For testing purposes only.
        :param perPage: number of collections to retrive per request. Default = 100
        :param output_file_path: path of the json file to save the collection slugs in.
        """
        assert(perPage >= 1 and perPage <= 100), "Number of results per page must be between 1 and 100"
        i = 0
        next_page_file = './next_page/collections.txt'
        url = self.base_url + 'collections'
        params = {}
        if self.chain:
            params['chain'] = self.chain
        params['limit'] = perPage
        try:
            with open(next_page_file) as f:
                params['next'] = f.readlines()[-1]
                print(params['next'])
                print(params['next'])
                print(params['next'])
                print(params['next'])
                print(params['next'])
        except:
            pass
        r = requests.get(url, headers = self.headers, params = params).json()
        # with open(output_file_path, 'w') as f:
            # append_data_to_file()
        collection_slugs = [collection['collection'] for collection in r['collections']]
        append_data_to_file(file_path = output_file_path, new_data = collection_slugs)
        params['next'] = r['next']
        print(params['next'])
        self._save_next_page(next_page_file, params['next'])
        i += 1
        while params['next'] and i is not num_req:
            r = requests.get(url, headers = self.headers, params = params).json()
            append_data_to_file(file_path = output_file_path, new_data = collection_slugs)
            self._save_next_page(next_page_file, params['next'])
            params = r['next']
            i += 1
            print(f"Saved page {i}")
        
        print(f"Total pages saved: {i}")
    
    def get_collection(self, collection_slug, output_file_path: str = "./data/opensea_collections.json"):
        """
        saves the collection metdata for a single colection
        :param collection_slug: uniques opensea identifier of the collection to save
        :param output_file_path: path of the file contiaining the collection metadata
        """
        assert(isinstance(collection_slug, str) and collection_slug), "Please specify a collection slug"
        url = self.base_url + f'collections/{collection_slug}'
        r = requests.get(url, headers = self.headers).json()
        append_data_to_file(output_file_path, r)
        return r
    
    def save_collections(self, collection_slug_file: str = "./data/opensea_collection_slugs.json", output_file_path: str = "./data/opensea_collections.json", num_req: int = None, perPage: int = 100):
        """
        Saves the collection metadata from opnesea in the output file path
        :param collection_slug_file: a json file containing the list of collection slugs to get the metadata of
        :param output_file_path: path of the file to save te collectio data to. Should be json.
        """
        if not os.path.exists(collection_slug_file):
            self.get_collections(num_req = num_req, perPage = perPage, output_file_path = collection_slug_file)
        
        with open(collection_slug_file, 'r') as f:
            slugs = json.loads(f.read())
        n = len(slugs)
        
        for i in range(n):
            if i is num_req:
                break
            self.get_collection(slugs[i], output_file_path = output_file_path)
            print(f"Saved collection {i}: {slugs[i]}")
        print(f"Saved collection data. Total collections {n}")
    
    def save_nfts_for_collection(self, collection_slug: str, perPage: int = 200, num_req: int = 2):
        """
        saves the nfts for the given collection in specified file path
        :param collection_slug: unique identifier for the collection on opnesea
        :param perPage: limit of NFTs to retireve per request. Limit parameter in the API. Maximum 200
        :param num_req: number of pages to retrieve. Only for testing purposes
        """
        assert(perPage >= 1 and perPage <= 200), "Number of results returned per page should be between 1 and 200"
        url = self.base_url + f'collection/{collection_slug}/nfts'
        i = 0
        output_file_path = f'./data/opensea/nfts/{collection_slug}_nfts.json'
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
            r = requests.get(url, headers = self.headers).json()
            append_data_to_file(output_file_path, r['nfts'])
            params['next'] = r['next']
            self._save_next_page(next_page_file, params['next'])
            i += 1
            if i == num_req:
                break
            print(f"Saved page {i}")
        
        print(f"Saved nfts for {collection_slug}. Total {i} pages")
    
    def get_collections_from_contracts(self, contract_file = './data/initial_top_10_games_contracts.txt', output_file = './data/collection_from_contracts.json'):
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
        pprint(contracts)
        for address in contracts:
            pprint(url.format(address))
            collection = requests.get(url.format(address), headers = self.headers).json()['collection']
            collections.add(collection)
        append_data_to_file(file_path = output_file, new_data = list(collections))
        print(f"Saved in {output_file}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chain', help = "Chain to restrict the results to", default = None)
    parser.add_argument('--limit_c', help = "limit for collections endpoint", default = 100)
    parser.add_argument('--limit_n', help = "limit for nfts endpoint", default = 200)
    parser.add_argument('--test_n', help = "number of requests for testsing", default = 2)

    args = parser.parse_args().__dict__
    consumer = OpenSea(args['chain'])
    # consumer.save_collections(perPage = args['limit_c'], num_req = int(args['test_n']))
    # consumer.get_collection('the-sandbox-assets')
    # consumer.save_nfts_for_collection(perPage=args['limit_n'], collection_slug='gods-unchained')
    consumer.get_collections_from_contracts()

if __name__ == "__main__":
    main()