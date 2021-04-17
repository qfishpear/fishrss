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

_SUPPORTED_SITES = set(["red", "dic"])
# api/filter相关
def get_api(site, **kwargs):
    assert site in CONFIG.keys(), "找不到{}的配置信息".format(site)
    assert site in _SUPPORTED_SITES, "不支持的网站：{}".format(site)
    if site == "red":
        RED = CONFIG["red"]
        api = REDApi(
            apikey=RED["api_key"],
            cookies=RED["cookies"] if "cookies" in RED.keys() else None,
            logger=logger,
            cache_dir=RED["api_cache_dir"],
            timeout=CONFIG["requests_timeout"],
            **kwargs,
        )
    elif site == "dic":
        DIC = CONFIG["dic"]
        api = DICApi(
            cookies=DIC["cookies"],
            logger=logger,
            cache_dir=DIC["api_cache_dir"],
            timeout=CONFIG["requests_timeout"],
            **kwargs,
        )
    return api
def get_filter(site):
    assert site in CONFIG.keys(), "找不到{}的配置信息".format(site)
    assert site in _SUPPORTED_SITES, "不支持的网站：{}".format(site)
    f = TorrentFilter(
        config=CONFIG[site]["filter_config"],
        logger=logger,
    )
    return f

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