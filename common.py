import os
import sys
import logging
import traceback
import base64
import urllib

from torrent_filter import TorrentFilter
from gzapi import REDApi, DICApi
from config import CONFIG

# logger相关
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)
log_stream = open(CONFIG["log_file"], "a")
filehandler = logging.StreamHandler(log_stream)
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

# api/filter相关
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

# 常数
CONST = {
    "dic_url": "dicmusic.club",
    "dic_tracker": "tracker.dicmusic.club",
    "red_url": "redacted.ch",
    "red_tracker": "flacsfor.me",
}

# 杂项，通用函数
def get_domain_name_from_url(url):
    return urllib.parse.urlparse(url).netloc