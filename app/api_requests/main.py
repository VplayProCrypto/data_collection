import requests
import json
import os
from pprint import pprint
import argparse
import time
from datetime import datetime, date, timedelta
# from utils import append_data_to_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chain', help = "Chain to restrict the results to", default = None)
    parser.add_argument('--limit_c', help = "limit for collections endpoint", default = 100)
    parser.add_argument('--limit_n', help = "limit for nfts endpoint", default = 200)
    parser.add_argument('--test_n', help = "number of requests for testsing", default = 2)

    args = parser.parse_args()
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
    txs = alchemy.get_nft_transfers('0xa342f5d851e866e18ff98f351f2c6637f4478db5', from_block = 0, per_page = 1000, chain = args.chain)
    sales = alchemy.get_nft_sales('0xa342f5d851e866e18ff98f351f2c6637f4478db5', from_block = 0, per_page = 1000, chain = args.chain)
    timestamp = alchemy.timestamp_from_block(11668641)
    print('-'*50)
    print(f'NFT sales: {len(sales["sales"])}')
    print(f'NFT transfers: {len(txs["transfers"])}')
    print('sale:', sales['sales'][0])
    print('transfer:', txs['transfers'][0])
    print(timestamp)
    print('-'*50)
    print(f'time: {time.time() - t}')

if __name__ == "__main__":
    main()