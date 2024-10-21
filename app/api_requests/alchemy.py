import requests
import json
import os
from pprint import pprint
import argparse
import time
from datetime import datetime, date, timedelta
from sqlmodel import Session
import keys
from orm.models import NFT, NFTEvent
# from utils import append_data_to_file

class Alchemy:
    def __init__(self):
        self.api_key = os.environ.get("ALCHEMY_API_KEY")
        self.api_key = keys.alchemy_api_key
        self.base_url = "https://{chain}.g.alchemy.com/"
        self.headers = {"accept": "application/json"}
        self.supported_chains = [
            "eth-mainnet",
            "polygon-mainnet",
            "arb-mainnet",
            "starknet-mainnet",
            "opt-mainnet",
        ]

    def get_nft_sales(
        self,
        contract_address: str,
        from_block: int = 0,
        next_page: str | None = None,
        chain: str = "eth-mainnet",
        per_page: int = 1000
    ):
        assert (
            chain in self.supported_chains
        ), "Chain not supported. Valid options: eth-mainnet, polygon-mainnet, arb-mainnet, starknet-mainnet, opt-mainnet"

        url = self.base_url.format(chain=chain) + f"nft/v3/{self.api_key}/getNFTSales"

        params = {
            "contractAddress": contract_address,
            "taker": "BUYER",
            "fromBlock": hex(from_block),
            "order": "asc",
            "limit": per_page,
        }

        if next_page:
            params["pageKey"] = next_page
        
        # print('--------------------------------------------------------------')
        # pprint(params)
        # print('--------------------------------------------------------------')

        response = requests.get(url, headers=self.headers, params=params).json()
        # pprint(response.keys())
        # print(response.url)
        

        return {"sales": response['nftSales'], "next_page": response["pageKey"]}
    
    def get_nft_sales_new(
        self,
        contract_address: str,
        from_block: int = 0,
        next_page: str | None = None,
        chain: str = "eth-mainnet",
        per_page: int = 1000,
        collection_slug: str = "",
        game_id: str = "",
    ):
        assert (
            chain in self.supported_chains
        ), "Chain not supported. Valid options: eth-mainnet, polygon-mainnet, arb-mainnet, starknet-mainnet, opt-mainnet"

        url = self.base_url.format(chain=chain) + f"nft/v3/{self.api_key}/getNFTSales"

        params = {
            "contractAddress": contract_address,
            "taker": "BUYER",
            "fromBlock": from_block,
            "order": "asc",
            "limit": per_page,
        }

        if next_page:
            params["pageKey"] = next_page

        response = requests.get(url, headers=self.headers, params=params).json()

        sales = [
            NFTEvent(
                transaction_hash=sale_data["transactionHash"],
                token_id=sale_data["tokenId"],
                contract_address=sale_data["contractAddress"],
                event_timestamp=datetime.fromtimestamp(
                    self.timestamp_from_block(sale_data["blockNumber"])
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
            for sale_data in response["nftSales"]
        ]

        return {"sales": sales, "next_page": response["pageKey"]}

    def save_all_nft_sales_for_contract(
        self,
        db: Session,
        contract_address: str,
        collection_slug: str,
        game_id: str,
        from_block: int = 0,
        next_page: str = "start",
        chain: str = "eth-mainnet",
    ):
        assert (
            chain in self.supported_chains
        ), "Chain not supported. Valid options: eth-mainnet, polygon-mainnet, arb-mainnet, starknet-mainnet, opt-mainnet"

        url = (
            self.base_url.format(chain=chain) + f"nft/v3/{self.api_key}/getNFTSales"
        )
        params = {
            "contractAddress": contract_address,
            "taker": "BUYER",
            "fromBlock": from_block,
            "order": "asc",
            "limit": 2,
        }

        i = 0
        if next_page != "start":
            params["pageKey"] = next_page


        while True:
            response: dict = requests.get(url, headers=self.headers, params=params).json()
            if response.get("nftSales"):
                for sale_data in response["nftSales"]:
                    # print(datetime.fromtimestamp(self.timestamp_from_block(sale_data["blockNumber"])))
                    db.add(NFTEvent(
                        transaction_hash=sale_data["transactionHash"],
                        token_id=sale_data["tokenId"],
                        contract_address=sale_data["contractAddress"],
                        event_timestamp=datetime.fromtimestamp(
                            self.timestamp_from_block(sale_data["blockNumber"])
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
                    ))
                    # print('-'*100)
                    # print('save nft sale')
                    # print(sale.event_timestamp)
                    # print('-'*100)
                db.commit()
                i += 1
                next_page = response.get("pageKey")
                params["pageKey"] = next_page
                print(f"Next page: {next_page}. Total saved: {i * 2}")
                if not next_page or not response.get('nftSales'):
                    break

            # if next_page:
            #     self.save_all_nft_sales_for_contract(
            #         db,
            #         contract_address,
            #         collection_slug,
            #         game_id,
            #         from_block,
            #         next_page,
            #         chain,
            #     )
        db.close()
        print(f"No more NFT sales found for contract {contract_address}.")

    def get_nft_transfers(
        self,
        contract_address: str,
        from_block: int = 0,
        per_page: int = 1000,
        chain: str = "eth-mainmet",
        next_page: str | None = None
    ):
        assert (
            chain in self.supported_chains
        ), "Chain not supported. Valid options: eth-mainnet, polygon-mainnet, arb-mainnet, starknet-mainnet, opt-mainnet"

        max_count = hex(per_page)
        from_block_hex = hex(from_block)
        category = ["erc721", "erc1155", "specialnft"]

        url = self.base_url.format(chain=chain) + f"v2/{self.api_key}"

        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "alchemy_getAssetTransfers",
            "params": [
                {
                    "fromBlock": from_block_hex,
                    "toBlock": "latest",
                    "contractAddresses": [contract_address],
                    "category": category,
                    "withMetadata": True,
                    "excludeZeroValue": True,
                    "maxCount": max_count,
                }
            ],
        }

        if next_page:
            payload["params"][0]["pageKey"] = next_page

        response = requests.post(url, headers=self.headers, json=payload).json()
        # pprint(response['result']['transfers'][0])
        print(response.keys(), response['result'].keys())
        return {"transfers": response['result']['transfers'], "next_page": response["result"].get("pageKey")}
    
    def get_nft_transfers_new(
        self,
        contract_address: str,
        from_block: int = 0,
        per_page: int = 1000,
        chain: str = "eth-mainmet",
        next_page: str | None = None,
        collection_slug: str = "",
        game_id: str = "",
    ):
        assert (
            chain in self.supported_chains
        ), "Chain not supported. Valid options: eth-mainnet, polygon-mainnet, arb-mainnet, starknet-mainnet, opt-mainnet"

        max_count = hex(per_page)
        from_block = hex(from_block)
        category = ["erc721", "erc1155", "specialnft"]

        url = self.base_url.format(chain=chain) + f"v2/{self.api_key}"

        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "alchemy_getAssetTransfers",
            "params": [
                {
                    "fromBlock": from_block,
                    "toBlock": "latest",
                    "contractAddresses": [contract_address],
                    "category": category,
                    "withMetadata": True,
                    "excludeZeroValue": True,
                    "maxCount": max_count,
                }
            ],
        }

        if next_page:
            payload["params"][0]["pageKey"] = next_page

        response = requests.post(url, headers=self.headers, json=payload).json()

        transfers = []

        for transfer_data in response["result"]["transfers"]:
            if transfer_data["category"] == "erc721":
                transfer = NFTEvent(
                    transaction_hash=transfer_data["hash"],
                    token_id=str(int(transfer_data["erc721TokenId"], 16)),
                    contract_address=transfer_data["rawContract"]["address"],
                    event_timestamp=datetime.fromisoformat(
                        transfer_data["metadata"]["blockTimestamp"][:-1]
                    ),
                    buyer=transfer_data["to"],
                    block_number=int(transfer_data["blockNum"], 16),
                    seller=transfer_data["from"],
                    price_val="0",
                    quantity=1,
                    price_currency=None,
                    price_decimals=None,
                    event_type="transfer",
                    collection_slug=collection_slug,
                    game_id=game_id,
                    marketplace=None,
                    marketplace_address=None,
                )
                transfers.append(transfer)
            elif transfer_data["category"] == "erc1155":
                for nft_metadata in transfer_data["erc1155Metadata"]:
                    transfer = NFTEvent(
                        transaction_hash=transfer_data["hash"],
                        token_id=str(int(nft_metadata["tokenId"], 16)),
                        contract_address=transfer_data["rawContract"]["address"],
                        event_timestamp=datetime.fromisoformat(
                            transfer_data["metadata"]["blockTimestamp"][:-1]
                        ),
                        buyer=transfer_data["to"],
                        block_number=int(transfer_data["blockNum"], 16),
                        seller=transfer_data["from"],
                        price_val="0",
                        quantity=int(nft_metadata["value"], 16),
                        price_currency=None,
                        price_decimals=None,
                        event_type="transfer",
                        collection_slug=collection_slug,
                        game_id=game_id,
                        marketplace=None,
                        marketplace_address=None,
                    )
                    transfers.append(transfer)

        return {"transfers": transfers, "next_page": response["result"]["pageKey"]}

    def save_all_nft_transfers_for_contract(
        self,
        db: Session,
        contract_address: str,
        collection_slug: str,
        game_id: str,
        from_block: int = 0,
        per_page: int = 1000,
        chain: str = "eth-mainnet",
        next_page: str = "start",
    ):
        assert (
            chain in self.supported_chains
        ), "Chain not supported. Valid options: eth-mainnet, polygon-mainnet, arb-mainnet, starknet-mainnet, opt-mainnet"

        max_count = hex(per_page)
        # from_block_hex = hex(from_block)
        category = ["erc721", "erc1155", "specialnft"]

        url = self.base_url.format(chain=chain) + f"v2/{self.api_key}"
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "alchemy_getAssetTransfers",
            "params": [
                {
                    "fromBlock": hex(from_block),
                    "toBlock": "latest",
                    "contractAddresses": [contract_address],
                    "category": category,
                    "withMetadata": True,
                    "excludeZeroValue": True,
                    "maxCount": max_count,
                }
            ],
        }

        if next_page != "start":
            payload["params"][0]["pageKey"] = next_page

        response = requests.post(url, headers=self.headers, json=payload).json()

        if response["result"].get("transfers"):
            for transfer_data in response["result"]["transfers"]:
                if transfer_data["category"] == "erc721":
                    transfer = NFTEvent(
                        transaction_hash=transfer_data["hash"],
                        token_id=str(int(transfer_data["erc721TokenId"], 16)),
                        contract_address=transfer_data["rawContract"]["address"],
                        event_timestamp=datetime.fromisoformat(
                            transfer_data["metadata"]["blockTimestamp"][:-1]
                        ),
                        buyer=transfer_data["to"],
                        block_number=int(transfer_data["blockNum"], 16),
                        seller=transfer_data["from"],
                        price_val="0",
                        quantity=1,
                        price_currency=None,
                        price_decimals=None,
                        event_type="transfer",
                        collection_slug=collection_slug,
                        game_id=game_id,
                        marketplace=None,
                        marketplace_address=None,
                    )
                    db.add(transfer)
                # db.commit()
                elif transfer_data["category"] == "erc1155":
                    for nft_metadata in transfer_data["erc1155Metadata"]:
                        transfer = NFTEvent(
                            transaction_hash=transfer_data["hash"],
                            token_id=str(int(nft_metadata["tokenId"], 16)),
                            contract_address=transfer_data["rawContract"]["address"],
                            event_timestamp=datetime.fromisoformat(
                                transfer_data["metadata"]["blockTimestamp"][:-1]
                            ),
                            buyer=transfer_data["to"],
                            block_number=int(transfer_data["blockNum"], 16),
                            seller=transfer_data["from"],
                            price_val="0",
                            quantity=int(nft_metadata["value"], 16),
                            price_currency=None,
                            price_decimals=None,
                            event_type="transfer",
                            collection_slug=collection_slug,
                            game_id=game_id,
                            marketplace=None,
                            marketplace_address=None,
                        )
                        db.add(transfer)
            db.commit()

            next_page = response["result"].get("pageKey")
            print(f"Next page: {next_page}")

            if next_page is not None:
                self.save_all_nft_transfers_for_contract(
                    db,
                    contract_address,
                    collection_slug,
                    game_id,
                    from_block,
                    per_page,
                    chain,
                    next_page,
                )
        else:
            print(f"No more NFT transfers found for contract {contract_address}.")

    def timestamp_from_block(self, block_num: int, chain: str = "eth-mainnet"):
        assert (
            chain in self.supported_chains
        ), "Chain not supported. Valid options: eth-mainnet, polygon-mainnet, arb-mainnet, starknet-mainnet, opt-mainnet"
        url = self.base_url.format(chain=chain) + f"v2/{self.api_key}"
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "eth_getBlockByNumber",
            "params": [hex(block_num), False],
        }
        r = requests.post(url, headers=self.headers, json=payload).json()
        t = int(r["result"]["timestamp"], 16)
        # print('-'*100)
        # print('timestamp from block')
        # print(t)
        # pprint(r)
        # print('-'*100)
        return t

    def _map_chain_to_alchemy_chain(self, chain: str):
        chain_mapping = {
            "ethereum": "eth-mainnet",
            "polygon": "polygon-mainnet",
            "arbitrum": "arb-mainnet",
        }
        alchemy_chain = chain_mapping.get(chain)
        if alchemy_chain is None:
            raise ValueError(f"Invalid chain: {chain}")
        return alchemy_chain

def main():
    blockn = 102948