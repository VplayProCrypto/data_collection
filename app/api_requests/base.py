from requests import Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from logging import Logger

logger = Logger(__name__)

class BaseAPI:
    def __init__(self):
        self.retry = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods={'GET', 'POST'},
        )
        self.session = Session()
        self.session.mount('https://', HTTPAdapter(max_retries=self.retry))
    
    def __del__(self):
        self.session.close()
        logger.info(f"Session closed for {self.__class__.__name__}")