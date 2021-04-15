import os
import json
import logging
import traceback
from IPython import embed

from gzapi import REDApi, Timer
from config import CONFIG

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, 
                    filename="/home7/fishpear/rss/transcode_scanner.log", filemode='a')

_RED = CONFIG["red"]
redapi = REDApi(
    apikey=_RED["api_key"],
    authkey=_RED["authkey"],
    torrent_pass=_RED["torrent_pass"],
    logger=logging.root,
    cache_dir=None,
)
redapi.timer = Timer(7, 10)


def is_same_release(t1, t2):
    return t1['media'] == t2['media'] and\
           t1['remasterYear'] == t2['remasterYear'] and\
           t1['remasterTitle'] == t2['remasterTitle'] and\
           t1['remasterRecordLabel'] == t2['remasterRecordLabel'] and\
           t1['remasterCatalogueNumber'] == t2['remasterCatalogueNumber']

RESULT_FILE = "./to_transcode.txt"
start_gid = 1230454

for gid in range(start_gid, start_gid + 100000):
    logging.info("dealing with gid {}".format(gid))
    try:
        js = redapi.query_gid(gid)
    except KeyboardInterrupt:
        logging.info(traceback.format_exc())
        exit(0)
    except:
        logging.info(traceback.format_exc())
        continue
    if js["status"] != "success":
        logging.info("groupid {} status: {}".format(gid, js["status"]))
        logging.info(json.dumps(js))
        continue
    tlist = js["response"]["torrents"]
    for t1 in tlist:
        if t1["format"] == "FLAC" and t1["encoding"] == "24bit Lossless":
            check = True
            for t2 in tlist:
                if t2 is not t1 and is_same_release(t1, t2) and t2["encoding"] == "Lossless":
                    check = False
                    break
            if check:
                tid = t1["id"]
                logging.info("found transcode target: gid {} tid {}".format(gid, tid))
                with open(RESULT_FILE, "a") as f:
                    f.write("https://redacted.ch/torrents.php?id={}&torrentid={}\n".format(gid, tid))