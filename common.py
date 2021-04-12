import requests
import xmltodict
import datasize
import os
import sys
import logging
import hashlib
import traceback
import time
import base64
import json
import urllib
from IPython import embed

from torrent_filter import TorrentFilter
from gzapi import REDApi, DICApi
from config import CONFIG

logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)

log_stream = open(CONFIG["log_file"], "a")
filehandler = logging.StreamHandler(log_stream)
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
filehandler.formatter = logging.Formatter(fmt=LOG_FORMAT)
filehandler.setLevel(logging.INFO)
logger.addHandler(filehandler)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logging.Formatter(fmt=LOG_FORMAT))
logger.addHandler(consoleHandler)
def flush_logger():
    log_stream.flush()
    os.fsync(log_stream)
    sys.stdout.flush()

if "red" in CONFIG.keys():
    _RED = CONFIG["red"]
    red_filter = TorrentFilter(
        config=_RED["filter_config"],
        logger=logger
    )
    redapi = REDApi(
        apikey=_RED["api_key"],
        authkey=_RED["authkey"],
        torrent_pass=_RED["torrent_pass"],
        logger=logger,
        cache_dir=_RED["api_cache_dir"]
    )

if "dic" in CONFIG.keys():
    _DIC = CONFIG["dic"]
    dic_filter = TorrentFilter(
        config=_DIC["filter_config"],
        logger=logger
    )
    dicapi = DICApi(
        authkey=_DIC["authkey"],
        cookies=_DIC["cookies"],
        torrent_pass=_DIC["torrent_pass"],
        logger=logger,
        cache_dir=_DIC["api_cache_dir"]
    )
