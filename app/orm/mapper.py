import json

from datetime import datetime, timedelta
from api_requests.alchemy import Alchemy
from api_requests.opensea import OpenSea
from api_requests.etherScan import EtherScan
from pprint import pprint
from copy import deepcopy
from utils import unflatten_nested_lists
from models import (
    Collection,
    CollectionDynamic,
    Contract,
    Event,
    Fee,
    NFT,
    NFTListing,
    NFTOffer,
    PaymentToken,
    TokenPrice,
    NFTOwnership,
    Erc20Transfer,
)


class Mapper:
    def __init__(
        self,
        eth_api_key: str = None,
        alchemy_api_key: str = None,
        game_names_file: str = "./games.json",
    ):
        self.opensea = OpenSea()
        self.ethscan = EtherScan(eth_api_key)
        self.alchemy = Alchemy()

        with open(game_names_file) as f:
            self.games = json.loads(f.read())

    def _get_game_name(self, collection_slug: str):
        name = ""
        for i in self.games.keys():
            if i in collection_slug:
                name = self.games[i]

        return name

    def _get_game_id(self, collection_slug: str):
        for i in self.games.keys():
            if i in collection_slug:
                return i

    def map_opensea_collection(self, collection_data: dict) -> Collection:
        collection_slug = collection_data["collection"]
        game_name = self._get_game_name(collection_slug)
        game_id = self._get_game_id(collection_slug)

        return Collection(
            opensea_slug=collection_data["collection"],
            name=collection_data["name"],
            game_name=game_name,
            game_id=game_id,
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

    def map_collection_dynamic(
        self,
        collection_dynamic_data: dict,
        daily_uaw: int,
        monthly_uaw: int,
        total_wallets: int,
        twitter_sentiment: float,
        facebook_sentiment: float,
        instagram_sentiment: float,
        reddit_sentiment: float,
        discord_sentiment: float,
    ) -> CollectionDynamic:
        return CollectionDynamic(
            collection_slug=collection_data["collection"],
            game_id=self._get_game_id(collection_slug),
            total_average_price=collection_dynamic_data["total_average_price"],
            total_supply=collection_dynamic_data["total_supply"],
            total_volume=collection_dynamic_data["total_volume"],
            total_num_owners=collection_dynamic_data["total_num_owners"],
            total_sales=collection_dynamic_data["total_sales"],
            total_market_cap=collection_dynamic_data["total_market_cap"],
            sales=collection_dynamic_data["sales"],
            volume=collection_dynamic_data["volume"],
            floor_price=collection_dynamic_data["floor_price"],
            floor_price_currency=collection_dynamic_data["floor_price_currency"],
            average_price=collection_dynamic_data["average_price"],
            daily_uaw=daily_uaw,
            monthly_uaw=monthly_uaw,
            total_wallets=total_wallets,
            twitter_sentiment=twitter_sentiment,
            facebook_sentiment=facebook_sentiment,
            instagram_sentiment=instagram_sentiment,
            reddit_sentiment=reddit_sentiment,
            discord_sentiment=discord_sentiment,
        )

    def map_opensea_contract(
        self, contract_data: dict, collection_slug: str
    ) -> Contract:
        return Contract(
            collection_slug=collection_slug,
            contract_address=contract_data["address"],
            chain=contract_data["chain"],
        )

    def map_payment_tokens(self, token_data: dict) -> PaymentToken:
        return PaymentToken(
            collection_slug=token_data["collection_slug"],
            contract_address=token_data["contract_address"],
            symbol=token_data["symbol"],
            decimals=token_data["decimals"],
            chain=token_data["chain"],
        )

    def map_token_price(self, price_data: dict) -> TokenPrice:
        return TokenPrice(
            contract_address=price_data["contract_address"],
            eth_price=price_data["eth_price"],
            usdt_price=price_data["usdt_price"],
            usdt_conversion_price=price_data.get("usdt_conversion_price"),
            eth_conversion_price=price_data.get("eth_conversion_price"),
            event_timestamp=datetime.fromtimestamp(price_data["timestamp"]),
        )

    def map_chain_to_alchemy_chain(self, chain: str):
        if chain == "ethereum":
            return "eth-mainnet"
        elif chain == "polygon":
            return "polygon-mainnet"
        elif chain == "arbitum":
            return "arb-mainnet"
        # elif chain == 'polygon':
        #     return 'polygon-mainnet'
        # elif chain == 'polygon':
        #     return 'polygon-mainnet'
        else:
            raise ValueError(f"Invalid chain: {chain}")

    def map_etherscan_erc20_transfer(
        self, transfer_data: dict, collection_slug: str
    ) -> ERC20Transfer:
        return ERC20Transfer(
            buyer=transfer_data["to"],
            seller=transfer_data["from"],
            contract_address=transfer_data["contractAddress"],
            price=float(transfer_data["value"]),
            symbol=transfer_data["tokenSymbol"],
            decimals=int(transfer_data["tokenDecimal"]),
            transaction_hash=transfer_data["hash"],
            event_timestamp=datetime.fromtimestamp(int(transfer_data["timeStamp"])),
            collection_slug=collection_slug,
        )

    def map_opensea_fee(self, fee_data: dict, collection_slug: str) -> Fee:
        return Fee(
            collection_slug=collection_slug,
            fee=fee_data["fee"] / 10000,
            recipient=fee_data["recipient"],
        )

    def map_opensea_nft(self, nft_data: dict) -> NFT:
        collection_slug = nft_data["collection"]
        game_id = self._get_game_id(collection_slug)

        return NFT(
            collection_slug=nft_data["collection"],
            token_id=nft_data["identifier"],
            game_id=game_id,
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

    def map_alchemy_nft_sale(
        self, sale_data: dict, collection_slug: str, game_id: str
    ) -> NFTEvent:
        return NFTEvent(
            transaction_hash=sale_data["transactionHash"],
            token_id=sale_data["tokenId"],
            contract_address=sale_data["contractAddress"],
            event_timestamp=datetime.fromtimestamp(
                self.alchemy.timestamp_from_block(sale_data["blockNumber"])
            ),
            buyer=sale_data["buyerAddress"],
            block_number=sale_data["blockNumber"],
            seller=sale_data["sellerAddress"],
            price_val=sale_data["sellerFee"]["amount"],
            quantity=int(sale_data["quantity"]),
            price_currency=sale_data["sellerFee"]["symbol"],
            price_decimals=sale_data["sellerFee"]["decimals"],
            event_type="sale",
            collection_slug=collection_slug,
            game_id=game_id,
            marketplace=sale_data["marketplace"],
            marketplace_address=sale_data["marketplaceAddress"],
        )

    def map_alchemy_nft_transfer(
        self, transfer_data: dict, collection_slug: str, game_id: str
    ) -> Union[NFTEvent, List[NFTEvent]]:
        event = NFTEvent(
            transaction_hash=transfer_data["hash"],
            token_id=None,
            contract_address=transfer_data["rawContract"]["address"],
            event_timestamp=datetime.fromisoformat(
                transfer_data["metadata"]["blockTimestamp"][:-1]
            ),
            buyer=transfer_data["to"],
            block_number=int(transfer_data["blockNum"], 16),
            seller=transfer_data["from"],
            price_val="0",
            quantity=0,
            price_currency=None,
            price_decimals=None,
            event_type="transfer",
            collection_slug=collection_slug,
            game_id=game_id,
            marketplace=None,
            marketplace_address=None,
        )

        if transfer_data["category"] == "erc721":
            event.token_id = str(int(transfer_data["erc721TokenId"], 16))
            event.quantity = 1
            return event
        elif transfer_data["category"] == "erc1155":
            events = []
            nfts = transfer_data["erc1155Metadata"]
            for i in nfts:
                event_copy = event.copy(deep=True)
                event_copy.token_id = str(int(i["tokenId"], 16))
                event_copy.quantity = int(i["value"], 16)
                events.append(event_copy)
            return events
        else:
            raise ValueError(f"Invalid category: {transfer_data['category']}")

    def map_opensea_listing(
        self, listing: dict, collection_slug: str, game_id: str
    ) -> NFTListing:
        return NFTListing(
            order_hash=listing["order_hash"],
            token_id=str(
                int(
                    listing["protocol_data"]["parameters"]["offer"][0][
                        "identifierOrCriteria"
                    ]
                )
            ),
            contract_address=listing["protocol_data"]["parameters"]["offer"][0][
                "token"
            ],
            collection_slug=collection_slug,
            game_id=game_id,
            seller=listing["protocol_data"]["parameters"]["offerer"],
            price_val=listing["price"]["current"]["value"],
            price_currency=listing["price"]["current"]["currency"],
            price_decimals=str(listing["price"]["current"]["decimals"]),
            start_date=datetime.fromtimestamp(
                int(listing["protocol_data"]["parameters"]["startTime"])
            ),
            expiration_date=datetime.fromtimestamp(
                int(listing["protocol_data"]["parameters"]["endTime"])
            ),
            event_timestamp=datetime.now(),
        )

    def map_opensea_offer(
        self, offer: dict, collection_slug: str, game_id: str
    ) -> NFTOffer:
        return NFTOffer(
            order_hash=offer["order_hash"],
            event_type="offer",
            token_id=str(int(offer["criteria"]["encoded_token_ids"])),
            contract_address=offer["criteria"]["contract"]["address"],
            collection_slug=collection_slug,
            game_id=game_id,
            seller=offer["protocol_data"]["parameters"]["offerer"],
            quantity=1,  # Assuming quantity is always 1 for offers
            price_val=offer["price"]["value"],
            price_currency=offer["price"]["currency"],
            price_decimals=str(offer["price"]["decimals"]),
            start_date=datetime.fromtimestamp(
                int(offer["protocol_data"]["parameters"]["startTime"])
            ),
            expiration_date=datetime.fromtimestamp(
                int(offer["protocol_data"]["parameters"]["endTime"])
            ),
            event_timestamp=datetime.now(),
        )

    def get_nfts_for_collection(
        self, collection_slug: str, num_pages: int = 10, next_page: str = None
    ):
        r = self.opensea.get_nfts_for_collection(
            collection_slug, num_pages=num_pages, next_page=next_page
        )
        r["nfts"] = [self.map_opensea_nft(i) for i in r["nfts"]]
        return r

    def get_collection(self, collection_slug: str):
        collection_data = self.opensea.get_collection(collection_slug)
        collection = self.map_opensea_collection(collection_data)
        fees = [
            self.map_opensea_fee(i, collection_slug) for i in collection_data["fees"]
        ]
        contracts = [
            self.map_opensea_contract(i, collection_slug)
            for i in collection_data["contracts"]
        ]
        return {"collection": collection, "fees": fees, "contracts": contracts}

    def get_nft_events_for_collection(
        self,
        collection_slug: str,
        game_id: str,
        contracts: list[dict],
        from_block: int,
        event_type: str = "transfer",
        max_recs: int = 1000,
        next_page: str | None = None,
    ):
        if event_type == "sale":
            for ca in contracts:
                # pprint(ca)
                r = self.alchemy.get_nft_sales(
                    ca["contract_address"],
                    from_block,
                    next_page=next_page,
                    chain=self.map_chain_to_alchemy_chain(ca["chain"]),
                    per_page=max_recs,
                )
                events = r["sales"]
                # print(len(events))
            events_mapped = [
                self.map_alchemy_nft_sale(i, collection_slug, game_id) for i in events
            ]
            return {
                "events": unflatten_nested_lists(events_mapped),
                "next_page": r["next_page"],
            }
        if event_type == "transfer":
            for ca in contracts:
                pprint(ca)
                r = self.alchemy.get_nft_transfers(
                    ca["contract_address"],
                    from_block,
                    next_page=next_page,
                    chain=self.map_chain_to_alchemy_chain(ca["chain"]),
                    per_page=max_recs,
                )
                events = r["transfers"]
            events_mapped = [
                self.map_alchemy_nft_transfer(i, collection_slug, game_id)
                for i in events
            ]
            return {
                "events": unflatten_nested_lists(events_mapped),
                "next_page": r["next_page"],
            }
        raise ValueError(f"Invalid event type: {event_type}")

    # def get_nft_events_for_collection(self, collection_slug: str, after_date: datetime, before_date: datetime, event_type: str = None, max_recs: int = 1000):
    #     events = self.opensea.get_events_for_collection(collection_slug, after_date, event_type = event_type, max_recs = max_recs, before_date = before_date)
    #     return [self.map_opensea_nft_event(i) for i in events]

    def get_erc20_transfers(
        self, contract_address: str, after_date: datetime, collection_slug: str
    ):
        transfers = self.ethscan.get_erc20_transfers(contract_address, after_date)
        return [
            self.map_etherscan_erc20_transfer(i, collection_slug) for i in transfers
        ]


def main():
    collection_slug = "the-sandbox-assets"
    mapper = Mapper()
    collection = mapper.get_collection(collection_slug)
    # nfts = mapper.get_nfts_for_collection(collection_slug, 2)
    # pprint(collection)
    # contracts = [mapper.map_opensea_contract(i, collection_slug) for i in collection['contracts']]
    e = mapper.get_nft_events_for_collection(
        collection_slug,
        "abcd",
        contracts=collection["contracts"],
        from_block=0,
        event_type="transfer",
        max_recs=100,
    )["events"]
    t = mapper.get_erc20_transfers(
        contract_address="0x3845badAde8e6dFF049820680d1F14bD3903a5d0",
        after_date=datetime.now() - timedelta(days=1),
        collection_slug=collection_slug,
    )
    # pprint(len(nfts['nfts']))
    # pprint(nfts['next_pages'])
    pprint(len(e))
    a = [i for i in e if i["quantity"] > 1]
    pprint(a[0])
    # pprint(e[1])
    # pprint(e[2])
    # pprint(len(t))
    # pprint(t[0])


if __name__ == "__main__":
    main()
