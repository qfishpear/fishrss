import requests
import json
import time
import os, sys
import logging
import traceback
import bencode
import hashlib
import urllib
from IPython import embed

from config import CONFIG
from common import logger, flush_logger
from torrent_filter import TorrentFilter
from gzapi import GazelleApi

configured_trackers = set()
try:
    from common import redapi, red_filter
    configured_trackers.add("red")
    logger.info("api and filter of RED are set")
except:
    logger.info("api or filter of RED is NOT set")
try:
    from common import dicapi, dic_filter
    configured_trackers.add("dic")
    logger.info("api and filter of DIC are set")
except:
    logger.info("api or filter of DIC is NOT set")

def get_info_hash(torrent):
    info = torrent["info"]
    info_raw = bencode.encode(info)
    sha = hashlib.sha1(info_raw)
    info_hash = sha.hexdigest()    
    return info_hash

def _handle(*,
            fname : str,
            torrent,
            api : GazelleApi,
            filter : TorrentFilter,
            token_thresh : tuple
    ):
    h = get_info_hash(torrent)
    tid = urllib.parse.parse_qs(urllib.parse.urlparse(torrent["comment"]).query)["torrentid"][0]
    logger.info("new torrent from {}: {} torrentid={} infohash={}".format(api.apiname, fname, tid, h))
    js = api.query_tid(tid)
    if js["status"] != "success":
        logger.info("error in js response: {}".format(json.dumps(js)))
        return 
    check_result = filter.check_json_response(js)
    if check_result != "accept":
        # 不满足条件
        logger.info("reject: {}".format(check_result))
    else:
        # 满足条件，转存种子
        logger.info("accept")
        dest_path = os.path.join(CONFIG["filter"]["dest_dir"], fname)
        with open(dest_path, "wb") as f:
            f.write(bencode.encode(torrent))
        # 根据体积限制使用令牌
        tsize = js["response"]["torrent"]["size"]
        if token_thresh is not None and token_thresh[0] < tsize and tsize < token_thresh[1]:
            fl_url = api.get_fl_url(tid)
            logger.info("getting fl:{}".format(fl_url))
            # 因为种子已转存，FL链接下载下来的种子会被丢弃
            requests.get(fl_url)

def handle_red(fname, torrent):    
    _handle(
        fname=fname,
        torrent=torrent,
        api=redapi,
        filter=red_filter,
        token_thresh=CONFIG["red"]["token_thresh"]
    )

def handle_dic(fname, torrent):
    _handle(
        fname=fname,
        torrent=torrent,
        api=dicapi,
        filter=dic_filter,
        token_thresh=CONFIG["dic"]["token_thresh"]
    )

def handle_default(fname, torrent):
    source = torrent["info"]["source"]
    logger.info("unconfigured source: {}, {} by default".format(source, CONFIG["filter"]["default_behavior"]))
    if CONFIG["filter"]["default_behavior"] == "accept":
        dest_path = os.path.join(CONFIG["filter"]["dest_dir"], fname)
        with open(dest_path, "wb") as f:
            f.write(bencode.encode(torrent))

def work():    
    flist = os.listdir(CONFIG["filter"]["source_dir"])
    if len(flist) == 0:
        return
    for fname in flist:
        tpath = os.path.join(CONFIG["filter"]["source_dir"], fname)
        if os.path.splitext(fname)[1] == ".torrent":            
            with open(tpath, "rb") as f:
                raw = f.read()
            os.remove(tpath)
            torrent = bencode.decode(raw)
            if "source" not in torrent["info"].keys():
                source = None
            else:
                source = torrent["info"]["source"]
            if source == "RED" and "red" in configured_trackers:
                handle_red(fname, torrent)
            elif source == "DICMusic" and "dic" in configured_trackers:
                handle_dic(fname, torrent)
            else:
                handle_default(fname, torrent)
    flush_logger()

cnt = 0
while True:
    try:
        work()
    except KeyboardInterrupt:
        logger.info(traceback.format_exc())
        exit(0)
    except:
        logger.info(traceback.format_exc())
        pass
    time.sleep(0.2)
    if cnt % 300 == 0:
        # 每分钟输出点东西，缓解黑屏焦虑
        logger.info("tick")
        flush_logger()
    cnt += 1