import requests
import json
import os
from pprint import pprint
import argparse
import time
from datetime import datetime, date, timedelta
from sqlmodel import Session
from orm.models import Collection, Fee, Contract, NFT, PaymentToken, NFTListing
import keys


class OpenSea:
    # class to consume the open sea API
    def __init__(self, chain: str = None):
        # :params chain: chain to search for. Default = None for searching all chains
        # self.base_url = os.environ.get('OPENSEA_BASE_URL')
        self.base_url = 'https://api.opensea.io/api/v2/'
        self.headers = {
            "accept": "application/json",
            # "x-api-key": os.environ.get("OPENSEA_API_KEY"),
            'x-api-key': keys.opensea_api_key
        }
        self.games = json.load(open('app/games.json'))
        # print(self.games)
        self.chain = chain

    def get_game_name(self, collection_slug: str, games: dict) -> str:
        for game_id in games.keys():
            if game_id in collection_slug:
                return games[game_id]['name']
        return ""

    def get_game_id(self, collection_slug: str, games: dict) -> str:
        for game_id in games.keys():
            if game_id in collection_slug:
                return game_id
        return ""

    def get_collection(self, collection_slug: str) -> dict:
        """
        Retrieves the collection metadata for a single collection.

        :param collection_slug: unique OpenSea identifier of the collection to save
        """
        assert (
            isinstance(collection_slug, str) and collection_slug
        ), "Please specify a collection slug"

        url = self.base_url + f"collections/{collection_slug}"
        collection_data: dict = requests.get(url, headers=self.headers).json()
        # pprint(collection_data)
        return collection_data


    def get_collection_new(self, collection_slug) -> dict:
        """
        Saves the collection metadata for a single collection.

        :param collection_slug: unique OpenSea identifier of the collection to save
        """
        assert (
            isinstance(collection_slug, str) and collection_slug
        ), "Please specify a collection slug"

        url = self.base_url + f"collections/{collection_slug}"
        collection_data: dict = requests.get(url, headers=self.headers).json()
        # pprint(collection_data)

        collection = Collection(
            opensea_slug=collection_data["collection"],
            name=collection_data["name"],
            game_name=self.get_game_name(collection_data["collection"], self.games),
            game_id=self.get_game_id(collection_data["collection"], self.games),
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
            created_date=datetime.fromisoformat(collection_data["created_date"]),
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

        if collection_data.get('payment_tokens'):
            payment_tokens = [
                PaymentToken(
                    collection_slug=collection_slug,
                    contract_address=payment_token_data["address"],
                    symbol=payment_token_data["symbol"],
                    decimals=payment_token_data["decimals"],
                    chain=payment_token_data["chain"],
                )
                for payment_token_data in collection_data["payment_tokens"]
            ]
        else:
            payment_tokens = []

        return {
            "collection": collection,
            "fees": fees,
            "contracts": contracts,
            "payment_tokens": payment_tokens,
            "game_id": collection.game_id
        }

    def save_all_nfts_for_collection(
        self,
        db: Session,
        collection_slug: str,
        next_page: str = "start",
        # should be enough to get all nfts and not crash our database
        pages: int = 100000,
    ):
        i = 0
        url = self.base_url + f"collection/{collection_slug}/nfts"
        params = {}
        if next_page != "start":
            params["next"] = next_page

        response: dict = requests.get(url, params=params, headers=self.headers).json()
        # pprint(response)

        if response.get("nfts"):
            for nft_data in response["nfts"]:
                nft = NFT(
                    collection_slug=nft_data["collection"],
                    token_id=nft_data["identifier"],
                    game_id=self.get_game_id(nft_data["collection"], self.games),
                    contract_address=nft_data["contract"],
                    name=nft_data["name"],
                    description=nft_data["description"],
                    image_url=nft_data["image_url"],
                    metadata_url=nft_data["metadata_url"],
                    opensea_url=nft_data["opensea_url"],
                    is_nsfw=nft_data["is_nsfw"],
                    is_disabled=nft_data["is_disabled"],
                    traits=nft_data.get("traits"),
                    token_standard=nft_data["token_standard"],
                    updated_at=datetime.fromisoformat(nft_data["updated_at"]),
                )
                db.add(nft)
            db.commit()

            next_page = response.get("next")
            print(f"Next page: {next_page}. Page number: {pages}")

            if next_page is not None and pages > 0:
                self.save_all_nfts_for_collection(
                    db, collection_slug, next_page, pages - 1
                )
            i += 1
        else:
            db.close()
            print(f"No more NFTs found for {collection_slug}.")

    def save_all_nft_listings_for_collection(
        self,
        db: Session,
        collection_slug: str,
        next_page: str = "start",
    ):
        url = self.base_url + f"listings/collection/{collection_slug}/all"
        params = {}

        if next_page != "start":
            params["next"] = next_page

        response: dict = requests.get(url, params=params, headers=self.headers).json()

        if response.get("listings"):
            for listing_data in response["listings"]:
                listing = NFTListing(
                    order_hash=listing_data["order_hash"],
                    token_id=listing_data["token_id"],
                    contract_address=listing_data["contract_address"],
                    collection_slug=collection_slug,
                    game_id=self.get_game_id(collection_slug, self.games),
                    seller=listing_data["seller"],
                    price_val=listing_data.get("price", {}).get("value"),
                    price_currency=listing_data.get("price", {}).get("currency"),
                    price_decimals=listing_data.get("price", {}).get("decimals"),
                    start_date=(
                        datetime.fromisoformat(listing_data["start_date"])
                        if listing_data.get("start_date")
                        else None
                    ),
                    expiration_date=(
                        datetime.fromisoformat(listing_data["expiration_date"])
                        if listing_data.get("expiration_date")
                        else None
                    ),
                    event_timestamp=datetime.fromisoformat(
                        listing_data["event_timestamp"]
                    ),
                )
                db.add(listing)
                db.commit()

            next_page = response.get("next")
            print(f"Next page: {next_page}")

            if next_page is not None:
                self.save_all_nft_listings_for_collection(
                    db, collection_slug, next_page
                )
        else:
            db.close()
            print(f"No more NFT listings found for {collection_slug}.")

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
            )

            pprint(response)
            response = response.json()
            if response.get("nfts"):
                nfts.extend(response['nfts'])

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

    def get_nfts_for_collection_new(
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
                            game_id=self.get_game_id(nft["collection"], self.games),
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
