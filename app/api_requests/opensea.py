import requests
import json
import os
from pprint import pprint
import argparse
import time
from datetime import datetime, date, timedelta
from orm.models import Collection, Fee, Contract, NFT


class OpenSea:
    # class to consume the open sea API
    def __init__(self, chain: str = None):
        # :params chain: chain to search for. Default = None for searching all chains
        self.base_url = os.environ.get("OPENSEA_BASE_URL")
        self.headers = {
            "accept": "application/json",
            "x-api-key": os.environ.get("OPENSEA_API_KEY"),
        }
        self.chain = chain

    def get_game_name(collection_slug: str, games: dict) -> str:
        for game_id in games.keys():
            if game_id in collection_slug:
                return games[game_id]
        return ""

    def get_game_id(collection_slug: str, games: dict) -> str:
        for game_id in games.keys():
            if game_id in collection_slug:
                return game_id
        return ""

    def get_collection(self, collection_slug) -> dict:
        """
        Saves the collection metadata for a single collection.

        :param collection_slug: unique OpenSea identifier of the collection to save
        """
        assert (
            isinstance(collection_slug, str) and collection_slug
        ), "Please specify a collection slug"

        url = self.base_url + f"collections/{collection_slug}"
        collection_data = requests.get(url, headers=self.headers).json()

        collection = Collection(
            opensea_slug=collection_data["collection"],
            name=collection_data["name"],
            game_name=get_game_name(collection_data["collection"], self.games),
            game_id=get_game_id(collection_data["collection"], self.games),
            description=collection_data["description"],
            owner=collection_data["owner"],
            category=collection_data["category"],
            is_nsfw=collection_data["is_nsfw"],
            opensea_url=collection_data["opensea_url"],
            project_url=collection_data["project_url"],
            wiki_url=collection_data["wiki_url"],
            discord_url=collection_data["discord_url"],
            telegram_url=collection_data["telegram_url"],
            twitter_url=collection_data["twitter_username"],
            instagram_url=collection_data["instagram_username"],
            created_date=collection_data["created_date"],
        )

        fees = [
            Fee(
                collection_slug=collection_slug,
                fee=fee_data["fee"] / 10000,
                recipient=fee_data["recipient"],
            )
            for fee_data in collection_data["fees"]
        ]

        contracts = [
            Contract(
                collection_slug=collection_slug,
                contract_address=contract_data["address"],
                chain=contract_data["chain"],
            )
            for contract_data in collection_data["contracts"]
        ]

        return {"collection": collection, "fees": fees, "contracts": contracts}

    def get_nfts_for_collection(
        self,
        collection_slug: str,
        num_pages: int,
        perPage: int = 200,
        next_page: str = None,
    ) -> dict:
        """
        Saves the NFTs for the given collection in the specified file path.

        :param collection_slug: unique identifier for the collection on OpenSea
        :param perPage: limit of NFTs to retrieve per request. Limit parameter in the API. Maximum 200
        :param num_pages: number of pages to retrieve. Only for testing purposes
        :param next_page: None for JSON save, otherwise SQL files
        """
        assert (
            perPage >= 1 and perPage <= 200
        ), "Number of results returned per page should be between 1 and 200"
        assert num_pages >= 1, "Number of pages should be at least one"

        url = self.base_url + f"collection/{collection_slug}/nfts"
        i = 0
        nfts = []
        next_pages = []
        params = {"limit": perPage}

        while True:
            if next_page:
                params["next"] = next_page

            response: dict = requests.get(
                url, params=params, headers=self.headers
            ).json()

            if response.get("nfts"):
                nfts.extend(
                    [
                        NFT(
                            collection_slug=nft["collection"],
                            token_id=nft["identifier"],
                            game_id=get_game_id(nft["collection"], self.games),
                            contract_address=nft["contract"],
                            name=nft["name"],
                            description=nft["description"],
                            image_url=nft["image_url"],
                            metadata_url=nft["metadata_url"],
                            opensea_url=nft["opensea_url"],
                            is_nsfw=nft["is_nsfw"],
                            is_disabled=nft["is_disabled"],
                            traits=nft.get("traits"),
                            token_standard=nft["token_standard"],
                            updated_at=datetime.fromisoformat(nft["updated_at"]),
                        )
                        for nft in response["nfts"]
                    ]
                )

                if response.get("next"):
                    params["next"] = response["next"]
                    next_pages.append(response.get("next"))
                else:
                    return {"nfts": nfts, "next_pages": next_pages}

            i += 1

            if i >= num_pages or not params.get("next"):
                break

            next_page = params["next"]

        print(f"Retrieved NFTs for {collection_slug}. Total {i} pages")
        return {"nfts": nfts, "next_pages": next_pages}

    def get_collections_from_contracts(
        self, contract_file="../data/initial_top_10_games_contracts.txt"
    ):
        """
        Saves the collection slugs for the given smart contracts into a json file. Appends into the existing file
        :param contract_file: the file containing the list of contracts. Must be a text file with one contract address on each line
        :param output_fie: the path for the file to save the collection slugs
        """
        with open(contract_file) as f:
            contracts = f.readlines()
        contracts = [c.strip("\n") for c in contracts]
        url = self.base_url + "/chain/ethereum" + "/contract/{0}"
        collections = set()
        # pprint(contracts)
        for address in contracts:
            # pprint(url.format(address))
            # time.sleep(0.1)
            collection = requests.get(url.format(address), headers=self.headers).json()[
                "collection"
            ]
            collections.add(collection)
        print(f"collections requested")
        return list(collections)

    def _filter_event(self, event: dict, collection_slug: str):
        if event["event_type"] == "order":
            return event["asset"]["collection"] == collection_slug
        else:
            return event["nft"]["collection"] == collection_slug

    def get_events_for_collection(
        self,
        collection_slug: str,
        after_date: datetime,
        before_date: datetime,
        event_type: str = None,
        max_recs: int = 1000,
    ) -> list:
        # assert(isinstance(event_type, str)), "Event type must be str"
        url = self.base_url + f"events/collection/{collection_slug}"
        i = 0
        params = {}
        events = []
        params["after"] = int(after_date.timestamp())
        if before_date:
            params["before"] = int(before_date.timestamp())
        if event_type:
            params["event_type"] = [event_type]
        else:
            params["event_type"] = ["sale", "listing", "transfer"]
        t = time.time()
        r = requests.get(url, params=params, headers=self.headers).json()
        # pprint(r)
        e = r.get("asset_events")
        if e:
            events.extend(e)
        else:
            return []
        params["next"] = r.get("next")
        i += 1
        print(f"retieived page {i}")
        while params["next"] and len(events) < max_recs:
            r = requests.get(url, headers=self.headers, params=params).json()
            e = r.get("asset_events")
            if e:
                e = [i for i in e if self._filter_event(i, collection_slug)]
                events.extend(e)
            else:
                break
            params["next"] = r.get("next")
            i += 1
            print(f"retieived page {i}")

        print(f"Total events retrieved: {len(events)} in time: {time.time() - t}")
        return events


# def save_collections(self, num_req: int = None, perPage: int = 100):
#     """
#     Saves the collection metadata from opnesea in the output file path
#     :param collection_slug_file: a json file containing the list of collection slugs to get the metadata of
#     :param output_file_path: path of the file to save te collectio data to. Should be json.
#     """
#     # if not os.path.exists(collection_slug_file):
#     #     self.get_collections(num_req = num_req, perPage = perPage, output_file_path = collection_slug_file)

#     # with open(collection_slug_file, 'r') as f:
#     #     slugs = json.loads(f.read())
#     slugs = self.get_collections_from_contracts()
#     n = len(slugs)
#     collections = []
#     for i in range(n):
#         if i is num_req:
#             break
#         collections.append(self.get_collection(slugs[i]))
#         print(f"Saved collection {i}: {slugs[i]}")
#     print(f"Saved collection data. Total collections {n}")
#     return collections


# def _save_next_page(self, file_path: str, next_page_link: str):
#     """ utility to save the next page link from previous response. To start from the new page every time. Reduces number of requests made.
#     :param file_path: path of the file to save the next page link
#     :param next_page_link: link to te next page
#     """

#     with open(file_path, 'a') as f:
#         f.write(next_page_link)
#         f.write('\n')

# def get_collections(self, num_req: int = None, perPage: int = 100) -> None:
#     """ Saves the collection slugs as a list in a json file
#     :param num_req: restricts the number of requests made, For testing purposes only.
#     :param perPage: number of collections to retrive per request. Default = 100
#     """
#     assert(perPage >= 1 and perPage <= 100), "Number of results per page must be between 1 and 100"
#     i = 0
#     next_page_file = '../next_page/collections.txt'
#     url = self.base_url + 'collections'
#     params = {}
#     if self.chain:
#         params['chain'] = self.chain
#     params['limit'] = perPage
#     try:
#         with open(next_page_file) as f:
#             params['next'] = f.readlines()[-1]
#             print(params['next'])
#             print(params['next'])
#             print(params['next'])
#             print(params['next'])
#             print(params['next'])
#     except:
#         pass
#     r = requests.get(url, headers = self.headers, params = params).json()
#     collection_slugs = [collection['collection'] for collection in r['collections']]
#     params['next'] = r['next']
#     # print(params['next'])
#     self._save_next_page(next_page_file, params['next'])
#     i += 1
#     while params['next'] and i is not num_req:
#         # time.sleep(0.1)
#         r = requests.get(url, headers = self.headers, params = params).json()
#         self._save_next_page(next_page_file, params['next'])
#         params = r['next']
#         i += 1
#         print(f"At page {i}")

#     print(f"Total pages: {i}")
# def _extract_offer_from_listing(self, listing):
#     assert(isinstance(listing, dict))
#     price_info = listing['price']['current']
#     p = listing['protocol_data']['parameters']
#     if len(p['offer']) > 1 or p['offer'][0]['item_tye'] in [1, 4, 5]:
#         return None
#     else:
#         item_info = {}
#         item_info['offerer'] = p['offerer']
#         item_info['contract'] = p['token']
#         item_info['token_id'] = p['identifierOrCriteria']
#         item_info['price'] = price_info['value'] / 10**price_info['decimals']
#         item_info['currency'] = price_info['currency']
#         return item_info

# def get_events_for_collection(self, collection_slug: str, after_date: datetime):
#     url = self.base_url + f'listings/collection/{collection_slug}/all'
#     if page == 0:
#         r = requests.get(url, headers = self.headers).json()
#     else:
#         try:
#             with open(next_page_file, 'r') as f:
#                 next_page = f.readlines()[page - 1]
#         except:
#             pass
#         params = {
#             'next': next_page
#         }
#         r = requests.get(url, headers = self.headers, params = params)
#     listings = r['listings']
#     next_page = r['next']
#     self._save_next_page(next_page_file, next_page)
#     nft_listings = [self._extract_offer_from_listing(l) for l in listings]
#     nft_listings = [i for i in nft_listings if i is not None]
#     while(next_page):
#         # time.sleep(0.1)
#         r = requests.get(url, headers = self.headers, params = params)
#         listings = r['listings']
#         next_page = r['next']
#         self._save_next_page(next_page_file, next_page)
#         nft_listings.extend([self._extract_offer_from_listing(l) for l in listings])
#         nft_listings = [i for i in nft_listings if i is not None]

#     return nft_listings

# def get_events_by_nft(self, token_id: str, contract_address: str, timeframe: int = 90, event_type: list = ["sale"]):
#     assert(not token_id == "" and not contract_address == ""), "Please provide token_id or contract addresses"
#     url = self.base_url + f'events/chain/{self.chain}/contract/{contract_address}/nfts/{token_id}'
#     after_time_stamp = time.mktime((date.today() - timedelta(days = timeframe)).timetuple())
#     params = {
#         'after': after_time_stamp,
#         'event_type': event_type
#     }
#     events = []
#     while True:
#         # time.sleep(0.1)
#         r = requests.get(url, headers = self.headers, params = params).json()
#         events.extend(r['asset_events'])
#         if not r['next']:
#             break
