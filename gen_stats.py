"""
deluge数据统计脚本
"""
import traceback
import deluge_client
import urllib
import functools
from IPython import embed

from config import CONFIG
import common
from common import logger, flush_logger
configured_sites = {}
for site in common.SITE_CONST.keys():
    try:
        # 如果只运行一次，则不验证登陆以减少延迟
        api = common.get_api(site)
        tfilter = common.get_filter(site)
        logger.info("api and filter of {} are set".format(site))
        configured_sites[site] = {"api":api, "filter":tfilter}
    except:
        logger.info("api or filter of {} is NOT set".format(site))

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
    site = common.get_tracker_site(t[b"tracker"].decode("utf-8"))
    if site not in configured_sites.keys():
        # unsupported tracker
        return {}
    else:
        api = configured_sites[site]["api"]
    comment = t[b"comment"].decode("utf-8")
    tid = urllib.parse.parse_qs(urllib.parse.urlparse(comment).query)["torrentid"][0]
    js = api.query_tid(tid)
    if js["status"] != "success":
        # torrentid is the only available info
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
        "tracker" : common.get_domain_name_from_url(t[b"tracker"].decode("utf-8")),
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
