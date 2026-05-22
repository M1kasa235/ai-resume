import logging
import sys

LOG_FORMAT = '%(asctime)s -  %(levelname)s - %(name)s - %(message)s'

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

logger= logging.getLogger(__name__)