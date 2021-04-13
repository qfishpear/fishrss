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
from common import logger, redapi, flush_logger

parser = argparse.ArgumentParser()
parser.add_argument('--stats', action='store_true', default=False,
                    help="show stats of all the uploaders")
args = parser.parse_args()

DIC_URL = "dicmusic.club"
RED_URL = "redacted.ch"

banlist = CONFIG["red"]["filter_config"]["banlist"]
api = redapi
NET_LOC = RED_URL
AUTOBAN = CONFIG["red"]["autoban"]

DELUGE = CONFIG["deluge"]
client = deluge_client.DelugeRPCClient(DELUGE["ip"], DELUGE["port"], DELUGE["username"], DELUGE["password"])
client.connect()
logger.info("autoban: deluge is connected: {}".format(client.connected))
assert client.connected

tlist = list(client.core.get_torrents_status({}, ["hash", "ratio", "progress", "total_size", "time_added", "comment"]).values())
uploaders = defaultdict(lambda: list())
now = time.time()
for t in tlist:
    comment = t[b"comment"].decode("utf-8")
    netloc = urllib.parse.urlparse(comment).netloc
    if netloc != NET_LOC:
        continue
    tid = urllib.parse.parse_qs(urllib.parse.urlparse(comment).query)["torrentid"][0]
    js = api.query_tid(tid)
    if js["status"] == "success":
        if t[b"progress"] / 100 >= AUTOBAN["ignore"]["min_progress"] and \
           now - t[b"time_added"] < AUTOBAN["ignore"]["max_time_added"]:
            uploaders[js["response"]["torrent"]["username"]].append(t)
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
                    uploader, len(torrents), ratio, total_ul/1024**3, total_size/1024**3))
                break

with open(banlist, "w") as f:
    for user in bannedusers:
        if len(user) > 1:
            f.write(user+"\n")
logger.info("{} user banned in total".format(len(bannedusers)))