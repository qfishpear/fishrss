"""
deluge数据统计脚本
"""
import traceback
import deluge_client
import urllib
import functools
from IPython import embed

from config import CONFIG
from common import logger, flush_logger, CONST, get_domain_name_from_url, get_api, get_filter
configured_trackers = set()
try:
    redapi = get_api("red")
    red_filter = get_filter("red")
    configured_trackers.add("red")
    logger.info("api and filter of RED are set")
except:
    logger.info("api or filter of RED is NOT set")
try:
    dicapi = get_api("dic")
    dic_filter = get_filter("dic")
    configured_trackers.add("dic")
    logger.info("api and filter of DIC are set")
except:
    logger.info("api or filter of DIC is NOT set")

DELUGE = CONFIG["deluge"]
client = deluge_client.DelugeRPCClient(DELUGE["ip"], DELUGE["port"], DELUGE["username"], DELUGE["password"])
client.connect()
logger.info("gen_stats: deluge is connected: {}".format(client.connected))

tlist = list(client.core.get_torrents_status({"state":"Seeding"}, [
    "hash",
    "name",
    "ratio",
    "total_size",
    "time_added",
    "comment",
    "tracker",
]).values())

"""
从网站api获取更多信息
"""
def gen_extra_info(t):
    tracker_url = urllib.parse.urlparse(t[b"tracker"].decode("utf-8")).netloc
    if "red" in configured_trackers and tracker_url == CONST["red_tracker"]:
        api = redapi
    elif "dic" in configured_trackers and tracker_url == CONST["dic_tracker"]:
        api = dicapi
    else:
        # unsupported tracker
        return {}
    comment = t[b"comment"].decode("utf-8")
    tid = urllib.parse.parse_qs(urllib.parse.urlparse(comment).query)["torrentid"][0]
    js = api.query_tid(tid)
    if js["status"] != "success":
        # 
        return {"torrentid":tid}
    response = js["response"]
    tinfo = response["torrent"]
    ginfo = response["group"]
    extra_info = {
        "uploader"    : tinfo["username"],
        "media"       : tinfo["media"],
        "format"      : tinfo["format"],
        "encoding"    : tinfo["encoding"],
        "releaseType" : ginfo["releaseType"],
        "remasterYear": tinfo["remasterYear"],
        "hasCue"      : tinfo["hasCue"],
        "hasLog"      : tinfo["hasLog"],
        "logScore"    : tinfo["logScore"],
        "torrentid"   : tid,
    }
    return extra_info

torrent_infos = []

for t in tlist:
    info = {
        "name" : t[b"name"].decode("utf-8"),
        "ratio" : t[b"ratio"],
        "tracker" : get_domain_name_from_url(t[b"tracker"].decode("utf-8")),
        "size": t[b"total_size"],
        "uploaded": int(t[b"total_size"] * t[b"ratio"]),
        "hash":  t[b"hash"].decode("utf-8"),
        "time_added":t[b"time_added"],
    }
    extra_info = gen_extra_info(t)
    info.update(extra_info)
    torrent_infos.append(info)

first_keys = ["tracker", "ratio", "uploaded", "size"]
last_keys = ["time_added", "hash", "name"]
keys = functools.reduce(lambda x,y: x.union(y), [set(info.keys()) for info in torrent_infos], set())
keys = first_keys + list(set(keys) - set(first_keys) - set(last_keys)) + last_keys
empty = {key:"" for key in keys}
print("\t".join(keys))
torrent_infos.sort(key=lambda info:info["time_added"])
for info in torrent_infos:
    complete_info = empty.copy()
    complete_info.update(info)
    print("\t".join([str(complete_info[key]) for key in keys]))
