"""
red自动ban人脚本，仅支持deluge
"""
import os
import traceback
import deluge_client
import time
import base64
import json
import urllib
import argparse
from IPython import embed
from collections import defaultdict

from config import CONFIG
from common import logger, redapi, flush_logger, CONST, get_domain_name_from_url

parser = argparse.ArgumentParser()
parser.add_argument('--stats', action='store_true', default=False,
                    help="show stats of all the uploaders")
args = parser.parse_args()

banlist = CONFIG["red"]["filter_config"]["banlist"]
api = redapi
SITE_DOMAIN_NAME = CONST["red_url"]
AUTOBAN = CONFIG["red"]["autoban"]

DELUGE = CONFIG["deluge"]
client = deluge_client.DelugeRPCClient(DELUGE["ip"], DELUGE["port"], DELUGE["username"], DELUGE["password"])
client.connect()
logger.info("autoban: deluge is connected: {}".format(client.connected))
assert client.connected

# 1. 从deluge获取必要信息
tlist = list(client.core.get_torrents_status({}, ["hash", "name", "ratio", "progress", "total_size", "time_added", "comment"]).values())
# 2. 按uploader分类
uploaders = defaultdict(lambda: list())
now = time.time()
for t in tlist:
    comment = t[b"comment"].decode("utf-8")
    if get_domain_name_from_url(comment) != SITE_DOMAIN_NAME:
        continue
    tid = urllib.parse.parse_qs(urllib.parse.urlparse(comment).query)["torrentid"][0]
    js = api.query_tid(tid)
    if js["status"] == "success":
        if t[b"progress"] / 100 >= AUTOBAN["ignore"]["min_progress"] and \
           now - t[b"time_added"] < AUTOBAN["ignore"]["max_time_added"]:
            uploaders[js["response"]["torrent"]["username"]].append(t)

# 3. 根据规则添加ban人
with open(banlist, "r") as f:
    bannedusers = set([line.strip() for line in f])    
for uploader, torrents in uploaders.items():
    if uploader not in bannedusers:
        total_ul = sum([t[b"total_size"] * t[b"ratio"] * t[b"progress"] / 100 for t in torrents])
        total_size = sum([t[b"total_size"] * t[b"progress"] / 100 for t in torrents])
        ratio = total_ul / total_size
        if args.stats:
            logger.info("uploader: {} #torrents: {} ratio: {:.3f} {:.3f}GB/{:.3f}GB".format(
                uploader, len(torrents), ratio, total_ul/1024**3, total_size/1024**3))
        for cond in AUTOBAN["ratio"]:
            if len(torrents) >= cond["count"] and ratio < cond["ratiolim"]:
                bannedusers.add(uploader)
                logger.info("new user banned: {} #torrents: {} ratio: {:.3f} {:.3f}GB/{:.3f}GB".format(
                    uploader, len(torrents), ratio, total_ul/1024**3, total_size/1024**3
                ))
                for t in torrents:
                    logger.info("related torrents: {} ratio: {:.3f} {:.1f}MB/{:.1f}MB".format(
                        t[b"name"].decode("utf-8"), t[b"ratio"], 
                        t[b"ratio"] * t[b"total_size"] / 1024**2, t[b"total_size"] / 1024**2
                    ))
                break
with open(banlist, "w") as f:
    for user in bannedusers:
        if len(user) > 1:
            f.write(user+"\n")
logger.info("{} user banned in total".format(len(bannedusers)))