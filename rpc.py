# from web3 import Web3, AsyncWeb3
import requests
from pprint import pprint

eth_url = "https://lb.drpc.org/ogrpc?network=ethereum&dkey=Aj5bpPGTU0Ido-vTc6yCowUjhYCxwK4R7p6yFjlcW9mh"

# eth_provider = Web3.HTTPProvider(eth_url)
# eth = Web3(eth_provider)

# print(eth.eth.get_block('latest'))

# headers = {
#     'content-type': 'application/json'
# }

# data = {"method": "eth_blockNumber","params": [], "id": "1", "jsonrpc": "2.0"}

# r = requests.post(eth_url, headers = headers, data = data)

# pprint(r)
# pprint(r.content)
# r.close()
