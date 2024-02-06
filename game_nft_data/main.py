#Getting data
import requests

url = "https://eth-mainnet.g.alchemy.com/nft/v3/docs-demo/getCollectionMetadata?collectionSlug=MaviaLand"
"https://eth-mainnet.g.alchemy.com/v2/test"

headers = {"accept": "application/json"}

response = requests.get(url, headers=headers)

print(response.text)