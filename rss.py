import requests
import hashlib
import logging
import bencode
import traceback
import os
import json
import time

#============================================================================
# 仅支持python3，依赖：
# pip3 install bencode.py requests
#============================================================================
# 这些字段需要你自己填写：
# cookie，从浏览器中复制，只需要cookie中的PHPSESSID和session两个字段
COOKIES = {"PHPSESSID": "xxxxxxxxxxxxxxxx",
           "session"  : "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}
# authkey和torrentpass：你可以从任意一个你的种子的下载链接里获得，长度均为32个字符
AUTHKEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TORRENT_PASS = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# 对于大于FL_THRESHOLD体积的种子使用免费令牌，单位字节Byte
# 建议第一次运行的时候不要修改这个值，这样就不会在老种上使用令牌，之后运行的时候再调小
FL_THRESHOLD = 100 * 1024**3 # 100GB
# 存储rss出来的种子的文件夹：
DOWNLOAD_DIR = "./watch/"
# 存储rss的log：
DOWNLOAD_LOG = "./downloaded.log"
#============================================================================


HEADERS = {
    'User-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
}

def get_info_hash(raw):
    info = bencode.decode(raw)["info"]
    info_raw = bencode.encode(info)
    sha = hashlib.sha1(info_raw)
    info_hash = sha.hexdigest()    
    return info_hash
def get_name(raw):
    info = bencode.decode(raw)["info"]
    return info["name"]

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT,
    filename="/home7/fishpear/rss/log.txt", filemode='a')
try:
    resp = requests.get("https://dicmusic.club/ajax.php?action=notifications", cookies=COOKIES, timeout=10)
    tlist = json.loads(resp.text)["response"]["results"]
except:
    logging.info("fail to read from RSS url")
    logging.info(traceback.format_exc())
    exit()
if not os.path.exists(DOWNLOAD_LOG):
    logging.info("log file doesn't exist, create new one: {}".format(DOWNLOAD_LOG))
    with open(DOWNLOAD_LOG, "w") as f:
        f.write("downloaded urls:\n")
with open(DOWNLOAD_LOG, "r") as f:
    downloaded = set([line.strip() for line in f])
if not os.path.exists(DOWNLOAD_DIR):
    logging.info("torrent directory doesn't exist, create new one: {}".format(DOWNLOAD_DIR))
    os.makedirs(DOWNLOAD_DIR)
logging.info("{} torrents in rss result".format(len(tlist)))
cnt = 0
now = time.time()
for t in tlist[:10]:
    tid = t["torrentId"]
    dl_url_raw = "https://dicmusic.club/torrents.php?action=download&id={}&authkey={}&torrent_pass={}".format(tid, AUTHKEY, TORRENT_PASS)
    if dl_url_raw in downloaded:
        continue
    if t["size"] > FL_THRESHOLD:
        dl_url = dl_url_raw + "&usetoken=1"
    else:
        dl_url = dl_url_raw
    try:
        logging.info("download {}".format(dl_url))
        resp = requests.get(dl_url, headers=HEADERS, timeout=120)
        raw = resp.content
        h = get_info_hash(raw)
        logging.info("hash={}".format(h))
        with open(DOWNLOAD_LOG, "a") as f:
            f.write("{}\n".format(dl_url_raw))
        with open(os.path.join(DOWNLOAD_DIR, "{}.torrent".format(get_name(raw))), "wb") as f:
            f.write(raw)
        cnt += 1
    except KeyboardInterrupt:
        break
    except:
        logging.info("fail to download:")
        logging.info(traceback.format_exc())        
logging.info("{} torrents added".format(cnt))
