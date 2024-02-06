# Setup
from web3 import Web3
from pprint import pprint

alchemy_url = "https://eth-mainnet.g.alchemy.com/v2/UJLNIFggw-fN1dgSj66CEPqIWKdpMeGP"
w3 = Web3(Web3.HTTPProvider(alchemy_url))

# Print if web3 is successfully connected
print(w3.isConnected())

# Get the latest block number
latest_block = w3.eth.getBlock("latest")
pprint(dict(latest_block))