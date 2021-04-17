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
parser.add_argument('--init', action='store_true', default=False,
                    help="run as initialization. "
                         "if not set, the autoban logic will ONLY ban an uploader if one of his uploaded torrents "
                         "is active. Here \"active\" is defined by being uploaded in an hour or not completed.")
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

now = time.time()

# 1. 从deluge获取必要信息
tlist = list(client.core.get_torrents_status({}, ["hash", "ratio", "progress", "total_size", "time_added", "comment"]).values())
logger.info("{} torrents in deluge".format(len(tlist)))
# 2. 按uploader分类
uploaders = defaultdict(lambda: list())
for t in tlist:
    comment = t[b"comment"].decode("utf-8")
    if get_domain_name_from_url(comment) != SITE_DOMAIN_NAME:
        continue
    tid = urllib.parse.parse_qs(urllib.parse.urlparse(comment).query)["torrentid"][0]
    js = api.query_tid(tid)
    if js["status"] == "success":
        uploaders[js["response"]["torrent"]["username"]].append(t)
uploaders = list(uploaders.items())
uploaders.sort(key=lambda kv: max([t[b"time_added"] for t in kv[1]]))

# 3. 根据规则添加ban人
with open(banlist, "r") as f:
    bannedusers = set([line.strip() for line in f])
for uploader, torrents in uploaders:
    if uploader not in bannedusers:
        # 根据规则忽略掉一些种子：
        counted_tlist = []
        for t in torrents:
            if t[b"progress"] / 100 >= AUTOBAN["ignore"]["min_progress"] and \
                now - t[b"time_added"] < AUTOBAN["ignore"]["max_time_added"]:
                counted_tlist.append(t)
        if len(counted_tlist) == 0:
            continue
        total_ul = sum([t[b"total_size"] * t[b"ratio"] * t[b"progress"] / 100 for t in counted_tlist])
        total_size = sum([t[b"total_size"] * t[b"progress"] / 100 for t in counted_tlist])
        ratio = total_ul / total_size
        if args.stats:
            logger.info("uploader: {} #torrents: {} ratio: {:.3f} {:.3f}GB/{:.3f}GB".format(
                uploader, len(torrents), ratio, total_ul / 1024**3, total_size / 1024**3))        
        if not args.init:
            # 如果不是作为初始化运行，则忽略最近没有新的活动种子的发种人
            # "活动"被定义为还未下载完成，或者添加时间未超过1小时
            # 这个功能是为了防止一些人因为"max_time_added"带来的滑动窗口而被ban。
            last_complete = max([t[b"time_added"] for t in torrents])
            min_progress = min([t[b"progress"] for t in torrents])
            if min_progress == 100 and now - last_complete > 1 * 60 * 60:
                # logger.info("{} is not checked: {}% {:.1f}hour".format(uploader, min_progress, (now - last_complete) / 60 / 60))
                continue
        # logger.info("{} is checked".format(uploader))
        for cond in AUTOBAN["ratio"]:
            if len(torrents) >= cond["count"] and ratio < cond["ratiolim"]:
                bannedusers.add(uploader)
                logger.info("new user banned: {} #torrents: {} ratio: {:.3f} {:.3f}GB/{:.3f}GB".format(
                    uploader, len(torrents), ratio, total_ul / 1024**3, total_size / 1024**3
                ))                
                for t in torrents:
                    tname = client.core.get_torrent_status(t[b"hash"], ["name"])[b"name"]
                    logger.info("related torrents: {} ratio: {:.3f} {:.1f}MB/{:.1f}MB".format(
                        tname.decode("utf-8"), t[b"ratio"], 
                        t[b"ratio"] * t[b"total_size"] * t[b"progress"] / 100 / 1024**2, 
                        t[b"total_size"] * t[b"progress"] / 100 / 1024**2,
                    ))
                break
with open(banlist, "w") as f:
    for user in sorted(list(bannedusers)):
        if len(user) > 1:
            f.write(user+"\n")
logger.info("{} user banned in total".format(len(bannedusers)))