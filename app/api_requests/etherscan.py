import requests
import json
import os
from pprint import pprint
import argparse
import time
from datetime import datetime, date, timedelta
from orm.models import ERC20Transfer
from sqlmodel import create_engine, Session


class EtherScan:
    def __init__(self):

        self.api_key = os.environ.get("ETHERSCAN_API_KEY")
        self.base_url = os.environ.get("ETHERSCAN_BASE_URL")
        self.headers = {
            "accept": "application/json",
        }

    def get_block_from_timestamp(self, timestamp: int):
        params = {
            "module": "block",
            "timestamp": str(timestamp),
            "action": "getblocknobytime",
            "closest": "before",
            "apiKey": self.api_key,
        }

        r = requests.get(self.base_url, params=params).json()
        return r["result"]

    def get_erc20_transfers(
        self, contract_address: str, after_date: datetime, collection_slug: str
    ):
        assert isinstance(
            contract_address, str
        ), "Please provide a valid contract address"

        block_num = self.get_block_from_timestamp(int(after_date.timestamp()))

        params = {
            "action": "tokentx",
            "module": "account",
            "contractaddress": contract_address,
            "sort": "asc",
            "apikey": self.api_key,
            "startblock": str(block_num),
        }

        response = requests.get(
            self.base_url, headers=self.headers, params=params
        ).json()

        transfers = [
            ERC20Transfer(
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
            for transfer_data in response["result"]
        ]

        return transfers

    def save_erc20_transfers(
        self,
        db: Session,
        contract_address: str,
        after_date: datetime,
        collection_slug: str,
    ):
        assert isinstance(
            contract_address, str
        ), "Please provide a valid contract address"

        block_num = self.get_block_from_timestamp(int(after_date.timestamp()))

        params = {
            "action": "tokentx",
            "module": "account",
            "contractaddress": contract_address,
            "sort": "asc",
            "apikey": self.api_key,
            "startblock": str(block_num),
        }

        response = requests.get(
            self.base_url, headers=self.headers, params=params
        ).json()

        for transfer_data in response["result"]:
            erc20transfer = ERC20Transfer(
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

            db.add(erc20transfer)
            db.commit()

        print("Added ERC20 transfers")
        db.close()
