import os
import sys
import logging
import traceback
import base64
import hashlib
import urllib
import bencode

# fix gbk problem on Windows
import _locale
_locale._getdefaultlocale = (lambda *args: ['en_US', 'utf8'])

from torrent_filter import TorrentFilter
from gzapi import REDApi, DICApi, OPSApi, SnakeApi
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

# 常数
SITE_CONST = {
    "dic":{
        "domain": "dicmusic.club",
        "tracker": "tracker.dicmusic.club",
        "source": "DICMusic",
    },
    "red":{
        "domain": "redacted.ch",
        "tracker": "flacsfor.me",
        "source": "RED",
    },
    "ops":{
        "domain": "orpheus.network",
        "tracker": "home.opsfet.ch",
        "source": "OPS",
    },
    "snake":{
        "domain": "snakepop.art",
        "tracker": "announce.snakepop.art",
        "source": "Snakepop",
    },
}
# api/filter相关
def get_api(site, **kwargs):
    assert site in CONFIG.keys(), "no configuration of {} found".format(site)
    assert site in SITE_CONST.keys(), "unsupported site: {}".format(site)
    if site == "red":
        RED = CONFIG["red"]
        api = REDApi(
            apikey=RED["api_key"],
            cookies=RED["cookies"] if "cookies" in RED.keys() else None,
            logger=logger,
            cache_dir=RED["api_cache_dir"],
            timeout=CONFIG["requests_timeout"],
            authkey=RED["authkey"],
            torrent_pass=RED["torrent_pass"],
            **kwargs,
        )
    elif site == "dic":
        DIC = CONFIG["dic"]
        api = DICApi(
            cookies=DIC["cookies"],
            logger=logger,
            cache_dir=DIC["api_cache_dir"],
            timeout=CONFIG["requests_timeout"],
            authkey=DIC["authkey"],
            torrent_pass=DIC["torrent_pass"],
            **kwargs,
        )
    elif site == "ops":
        OPS = CONFIG["ops"]
        api = OPSApi(
            apikey=OPS["api_key"],
            cookies=OPS["cookies"] if "cookies" in OPS.keys() else None,
            logger=logger,
            cache_dir=OPS["api_cache_dir"],
            timeout=CONFIG["requests_timeout"],
            authkey=OPS["authkey"],
            torrent_pass=OPS["torrent_pass"],
            **kwargs,
        )
    elif site == "snake":
        SNAKE = CONFIG["snake"]
        api = SnakeApi(
            cookies=SNAKE["cookies"],
            logger=logger,
            cache_dir=SNAKE["api_cache_dir"],
            timeout=CONFIG["requests_timeout"],
            authkey=SNAKE["authkey"],
            torrent_pass=SNAKE["torrent_pass"],
            **kwargs,
        )

    return api
def get_filter(site):
    assert site in CONFIG.keys(), "no configuration of {} found".format(site)
    assert site in SITE_CONST.keys(), "unsupported site: {}".format(site)
    f = TorrentFilter(
        config=CONFIG[site]["filter_config"],
        logger=logger,
    )
    return f

# 杂项，通用函数
def get_domain_name_from_url(url):
    return urllib.parse.urlparse(url).netloc
def get_params_from_url(url):
    return dict(urllib.parse.parse_qsl(urllib.parse.urlparse(url).query))
def get_info_hash(torrent):
    info = torrent["info"]
    info_raw = bencode.encode(info)
    sha = hashlib.sha1(info_raw)
    info_hash = sha.hexdigest()    
    return info_hash
def get_torrent_site(torrent):
    if "source" not in torrent["info"].keys():
        source = None
    else:
        source = torrent["info"]["source"]
    for site, sinfo in SITE_CONST.items():
        if source == sinfo["source"]:
            return site
    return "unknown"
def get_url_site(url):
    domain_name = get_domain_name_from_url(url)
    for site, sinfo in SITE_CONST.items():
        if domain_name == sinfo["domain"]:
            return site
    return "unknown"
def get_tracker_site(url):
    domain_name = get_domain_name_from_url(url)
    for site, sinfo in SITE_CONST.items():
        if domain_name == sinfo["tracker"]:
            return site
    return "unknown"
def error_catcher(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except KeyboardInterrupt:
        logger.info(traceback.format_exc())
        exit(0)
    except Exception as _:
        logger.info(traceback.format_exc())
        pass