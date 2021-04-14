"""
警告，此脚本会删除deluge内的种子和文件！
功能：删除所有deluge里"Tracker Status"中含有"Unregistered torrent"字样的种子，以及文件
"""

import traceback
import deluge_client
from IPython import embed

from config import CONFIG
from common import logger

DELUGE = CONFIG["deluge"]
client = deluge_client.DelugeRPCClient(DELUGE["ip"], DELUGE["port"], DELUGE["username"], DELUGE["password"])
client.connect()
logger.info("remove_unregistered: deluge is connected: {}".format(client.connected))

tlist = list(client.core.get_torrents_status({"state":"Downloading"}, ["hash", "name", "tracker_status"]).values())
for t in tlist:
    if "Unregistered torrent" in t[b"tracker_status"].decode("utf-8"):
        logger.info("removing torrent \"{}\" reason: \"{}\"".format(
            t[b"name"].decode("utf-8"), t[b"tracker_status"].decode("utf-8")))
        client.core.remove_torrent(t[b"hash"], True)
