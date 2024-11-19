# import requests
# from requests import Session
# from requests.adapters import HTTPAdapter
import aiohttp
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt
# from urllib3 import Retry
from logging import Logger

logger = Logger(__name__)

class BaseAPI:
    def __init__(self):
        self.session = None
        # self.retry = Retry(
        #     total=3,
        #     backoff_factor=0.1,
        #     status_forcelist=[429, 500, 502, 503, 504],
        #     allowed_methods={'GET', 'POST'},
        # )
        # self.session = Session()
        # self.session.mount('https://', HTTPAdapter(max_retries=self.retry))
    
    async def init_session(self):
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            logger.info(f"Session closed for {self.__class__.__name__}")
    
    # def __del__(self):
    #     self.session.close()
    
    # def get(self, url: str, params: dict = None):
    #     if params:
    #         return self.session.get(url, params = params).json()
    #     return self.session.get(url).json()

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    async def get(self, url: str, params: dict = None, headers: dict = None):
        await self.init_session()
        try:
            async with self.session.get(url = url, params = params, headers = headers) as response:
                response.raise_for_status()
                res = await response.json()
                print(f'Response: {res}')
                return res
        except aiohttp.ClientError as e:
            logger.error(f"Unable to fetch request: {e}")
            raise
    
    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    async def post(self, url: str, payload: dict, params: dict = None, headers: dict = None):
        # await self.init_session()
        try:
            async with self.session.post(url = url, json = payload, params = params, headers = headers) as response:
                response.raise_for_status()
                res = await response.json()
                # print('--------------------------------')
                # print(f'Response: {res}')
                # print('--------------------------------')
                return res
        except aiohttp.ClientError as e:
            logger.error(f"Unable to fetch request: {e}")
            raise

async def get_nft_traits(url: str, base: BaseAPI):
        try:
            # Step 1: Make the API request to get the metadata from the URL
            response_json: dict = await base.get(url)

            # Step 2: Validate the response is actually a dictionary
            if not isinstance(response_json, dict):
                raise ValueError(f"Unexpected response type: Expected dict, got {type(response_json)}")

            # Step 3: Attempt to retrieve the traits from various possible fields in the response
            traits: list[dict] = (
                response_json.get('attributes') or
                response_json.get('properties') or
                response_json.get('traits')
            )

            # Step 4: If traits are None, return an empty list to indicate no traits found
            if traits is None:
                self.logger.warning(f"No traits found in response for URL: {url}")
                return []

            # Step 5: Validate the traits is a list of dictionaries, as expected
            if not isinstance(traits, list) or not all(isinstance(trait, dict) for trait in traits):
                raise ValueError("Traits should be a list of dictionaries")

            print(traits)

        except Exception as e:
            # Handle any unexpected exceptions
            print(f"Error while retrieving traits for URL {url}: {e}")
            raise

async def main():
    base = BaseAPI()
    url = 'https://be.mavia.com/api/nft/metadata/{id}'
    token_ids = [str(i) for i in range(500, 600)]
    tasks = [get_nft_traits(url = url.format(id=i), base = base) for i in token_ids]
    await asyncio.gather(*tasks)
    await base.close_session()
    # from app.orm.postgres_injector_orm import Injector
    # injector = Injector()
    # injector.retrieve_missing_traits_all('mavia-land')


if __name__ == '__main__':
    asyncio.run(main())