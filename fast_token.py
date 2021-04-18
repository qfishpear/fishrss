import os
import argparse
import requests
import traceback
import bencode
import hashlib
import logging

from config import CONFIG
from common import logger

configured_trackers = set()
if "red" in CONFIG.keys():
    configured_trackers.add("red")
if "dic" in CONFIG.keys():
    configured_trackers.add("dic")

parser = argparse.ArgumentParser()
parser.add_argument('url', help="url of torrent, required")
parser.add_argument('--chromeheaders', action='store_true', default=False,
                    help="If set, requests will be sent with chrome's headers instead of"
                         "the default headers of Requests. "
                         "It can bypass site's downloading limit of non-browser downloading of torrents. "
                         "This is slightly against the rule of api usage, so add this only if necessary")
args = parser.parse_args()

if args.chromeheaders:
    HEADERS = {
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
    }
else:
    HEADERS = requests.utils.default_headers()

def get_info_hash(torrent):
    info_raw = bencode.encode(torrent["info"])
    sha = hashlib.sha1(info_raw)
    info_hash = sha.hexdigest()
    return info_hash
def handle(site, url, torrent):
    tsize = sum([f["length"] for f in torrent["info"]["files"]])
    token_thresh = CONFIG[site]["token_thresh"]
    if token_thresh[0] <= tsize and tsize <= token_thresh[1]:        
        fl_url = url + "&usetoken=1"
        logger.info("getting fl: {}".format(fl_url))
        sess = requests.Session()
        sess.mount('https://', requests.adapters.HTTPAdapter(max_retries=1))
        sess.mount('http://', requests.adapters.HTTPAdapter(max_retries=1))        
        # 因为种子已转存，FL链接下载下来的种子会被丢弃
        r = sess.get(fl_url, headers=HEADERS, timeout=CONFIG["requests_timeout"])
        try:
            # 验证种子合法性
            fl_torrent = bencode.decode(r.content)
            assert get_info_hash(torrent) == get_info_hash(fl_torrent)
        except:
            logger.info("Invalid torrent downloaded from fl_url. It might because you don't have ENOUGH tokens(可能令牌不足？):")
            logger.info(traceback.format_exc())
def work(url):
    logger.info("fast token: downloading from url: {}".format(url))
    r = requests.get(url, headers=HEADERS, timeout=CONFIG["requests_timeout"])
    raw = r.content
    torrent = bencode.decode(raw)
    # 无条件转存种子
    fname = "{}.torrent".format(get_info_hash(torrent))
    dest_dir = CONFIG["filter"]["dest_dir"]
    fpath = os.path.join(dest_dir, fname)
    logger.info("saving to {}".format(fpath))
    with open(fpath, "wb") as f:
        f.write(raw)
    # 使用令牌
    if "source" not in torrent["info"].keys():
        source = None
    else:
        source = torrent["info"]["source"]
    if source == "RED" and "red" in configured_trackers:
        handle("red", url, torrent)
    elif source == "DICMusic" and "dic" in configured_trackers:
        handle("dic", url, torrent)

try:
    work(args.url)
except:
    logger.info(traceback.format_exc())