import requests
from requests import Session
from requests.adapters import HTTPAdapter
import aiohttp
from tenacity import retry, wait_exponential, stop_after_attempt
from urllib3 import Retry
from logging import Logger

logger = Logger(__name__)

class BaseAPI:
    def __init__(self):
        self.session = None
        self.retry = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods={'GET', 'POST'},
        )
        self.session = Session()
        self.session.mount('https://', HTTPAdapter(max_retries=self.retry))
    
    def init_async_session(self):
        if not self.session or self.session.closed:
            self.async_session = aiohttp.ClientSession()
    
    def close_session(self):
        if self.session:
            self.session.close()
            logger.info(f"Session closed for {self.__class__.__name__}")
    
    async def close_session_async(self):
        if self.async_session:
            await self.async_session.close()
            logger.info(f"Async Session closed for {self.__class__.__name__}")
    
    # def __del__(self):
    #     self.session.close()
    
    # def get(self, url: str, params: dict = None):
    #     if params:
    #         return self.session.get(url, params = params).json()
    #     return self.session.get(url).json()

    # @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    def get(self, url: str, params: dict = None, headers: dict = None):
        # await self.init_session()
        try:
            with self.session.get(url = url, params = params, headers = headers) as response:
                response.raise_for_status()
                res = response.json()
                # print(f'Response: {res}')
                return res
        except requests.exceptions.RequestException as e:
            logger.error(f"Unable to fetch request: {e}")
            raise
    
    # @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    def post(self, url: str, payload: dict, params: dict = None, headers: dict = None):
        # await self.init_session()
        try:
            with self.session.post(url = url, json = payload, params = params, headers = headers) as response:
                response.raise_for_status()
                res = response.json()
                # print('--------------------------------')
                # print(f'Response: {res}')
                # print('--------------------------------')
                return res
        except requests.exceptions.RequestException as e:
            logger.error(f"Unable to fetch request: {e}")
            raise
    
    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    async def async_get(self, url: str, params: dict = None, headers: dict = None):
        await self.init_async_session()
        try:
            async with self.async_session.get(url = url, params = params, headers = headers) as response:
                response.raise_for_status()
                res = response.json()
                print(f'Response: {res}')
                return res
        except aiohttp.ClientError as e:
            logger.error(f"Unable to fetch request: {e}")
            raise
    
    # @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    async def async_post(self, url: str, payload: dict, params: dict = None, headers: dict = None):
        await self.init_async_session()
        try:
            async with self.async_session.post(url = url, json = payload, params = params, headers = headers) as response:
                response.raise_for_status()
                res = response.json()
                # print('--------------------------------')
                # print(f'Response: {res}')
                # print('--------------------------------')
                return res
        except aiohttp.ClientError as e:
            logger.error(f"Unable to fetch request: {e}")
            raise