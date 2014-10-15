# coding=utf-8
import logging
import os
import sys

__author__ = '4ikist'

flickr_api_key = '35d3ee874f13ee7de87df528254d0c75'
flickr_api_key_secret = '7dfae325a92a0c45'
flickr_base_url = 'https://api.flickr.com/services/rest/'
flickr_user_id = '127892511@N08'

photo_ids_ttl = 60
photo_data_ttl = 60*5


portfolio_tags = set(['portfolio'])


def module_path():
    if hasattr(sys, "frozen"):
        return os.path.dirname(
            unicode(sys.executable, sys.getfilesystemencoding())
        )
    return os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))

# настройки логирования
log_file = os.path.join(module_path(), 'result.log')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
fh = logging.FileHandler(log_file)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s[%(levelname)s]%(name)s %(threadName)s : %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)
logging.getLogger('requests.packages.urllib3.connectionpool').propagate = False
