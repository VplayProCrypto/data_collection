import requests
from pprint import pprint
import argparse

base_endpoint = "https://api.godsunchained.com/v0/"

def get_total_proto():
    url = base_endpoint + 'proto'
    r = requests.get(url)
    return r.json()['total']

def get_proto_details(id: int):
    url = base_endpoint + 'proto/{id}'
    return requests.get(url).json()

def get_proto_details_batch(page: int, perPage: int):
    url = base_endpoint + 'proto'
    params = {
        'page': page,
        'perPage': perPage
    }
    return requests.get(url, params = params).json()

def get_card_details():
    url = base_endpoint + 'card'
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--page', default=1)
    parser.add_argument('--perPage', default=100)
    args = parser.parse_args().__dict__

    pprint(get_proto_details_batch(args['page'], args['perPage']))

if __name__ == "__main__":
    main()