import logging
import sys

def setup_logging():
    formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    
    # Adjust the logging level of noisy libraries if necessary
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
