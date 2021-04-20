import requests
import json
import time
import os, sys
import logging
import traceback
import bencode
import hashlib
import urllib
import base64
import argparse
from multiprocessing.pool import ThreadPool
from IPython import embed

from config import CONFIG
import common
from common import logger
from torrent_filter import TorrentFilter
from gzapi import GazelleApi

parser = argparse.ArgumentParser()
parser.add_argument("--url", default=None, 
                     help="Download url of a torrent. If an url is provided, "
                     "the code will only run once for the provided url and exits.")
parser.add_argument("--file", default=None, 
                     help="path of a torrent file. If a file is provided, "
                     "the code will only run once for the provided file and exits.")
parser.add_argument("--skip-api", action="store_true", default=False,
                     help="If set, the site api call will be skipped. Notice: the api-only information "
                     "will be unavailable: uploader, media and format. Therefore, their filter config "
                     "must be None otherwise there won't be any torrent filtered out.")
parser.add_argument("--no-tick", action="store_true", default=False,
                    help="If not set, every minute there will be a \"tick\" shown in the log, "
                         "in order to save people with \"black screen anxiety\"")
parser.add_argument("--chromeheaders", action="store_true", default=False,
                    help="If set, torrent download requests will be sent with chrome's headers instead of"
                         "the default headers of Requests. "
                         "It can bypass site's downloading limit of non-browser downloading of torrents. "
                         "This is slightly against the rule of api usage, so add this only if necessary")
parser.add_argument("--force-accept", action="store_true", default=False,
                    help="If set, always accept a torrent regardless of filter's setting")
parser.add_argument("--deluge", action="store_true", default=False,
                    help="push to deluge by its api directly")
# parser.add_argument("--qbittorrent", action="store_true", default=False,
#                     help="push to qbittorrent by its api directly")
args = parser.parse_args()

run_once = args.url is not None or args.file is not None
if args.chromeheaders:
    download_headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'}
else:
    download_headers = requests.utils.default_headers()

if args.deluge:
    import deluge_client
    DELUGE = CONFIG["deluge"]
    # 本机的话这个延迟大概0.01s左右，就不并行了
    de = deluge_client.DelugeRPCClient(DELUGE["ip"], DELUGE["port"], DELUGE["username"], DELUGE["password"])
    de.connect()
    logger.info("deluge is connected: {}".format(de.connected))
    assert de.connected

configured_sites = {}
for site in common.SITE_CONST.keys():
    try:
        # 如果只运行一次，则不验证登陆以减少延迟
        api = common.get_api(site, skip_login=run_once)
        tfilter = common.get_filter(site)
        logger.info("api and filter of {} are set".format(site))
        configured_sites[site] = {"api":api, "filter":tfilter}
    except:
        logger.info("api or filter of {} is NOT set".format(site))

def handle_accept(torrent):
    fname = "{}.torrent".format(common.get_info_hash(torrent))
    if args.deluge:
        logger.info("pushing to deluge")
        raw = bencode.encode(torrent)
        de.core.add_torrent_file(fname, base64.b64encode(raw), {})
    else:
        # default: save to dest_dir
        save_path = os.path.join(CONFIG["filter"]["dest_dir"], fname)
        logger.info("saving to {}".format(save_path))
        with open(save_path, "wb") as f:
            f.write(bencode.encode(torrent))    

def _handle(*,
            torrent,
            tinfo,
            filter : TorrentFilter,
            token_thresh : tuple,
            fl_url=None
    ):
    logger.info("{} torrentid={} infohash={}".format(torrent["info"]["name"], tinfo["tid"], tinfo["hash"]))
    check_result = filter.check_tinfo(**tinfo)
    if check_result != "accept" and not args.force_accept:
        # 不满足条件
        logger.info("reject: {}".format(check_result))
    else:
        # 满足条件，转存种子        
        logger.info("accept")
        handle_accept(torrent)
        # 根据体积限制使用令牌
        if token_thresh is not None and token_thresh[0] < tinfo["size"] and tinfo["size"] < token_thresh[1]:
            if fl_url is None:
                logger.info("fl url not provided")
            else:
                logger.info("getting fl:{}".format(fl_url))
                # 因为种子已转存，FL链接下载下来的种子会被丢弃
                r = requests.get(fl_url, timeout=CONFIG["requests_timeout"], headers=download_headers)
                try:
                    # 验证种子合法性
                    fl_torrent = bencode.decode(r.content)
                    assert common.get_info_hash(torrent) == common.get_info_hash(fl_torrent)
                except:
                    logger.info("Invalid torrent downloaded from fl_url. It might because you don't have ENOUGH tokens(可能令牌不足？):")
                    logger.info(traceback.format_exc())

def handle_default(torrent):
    if args.force_accept:
        handle_accept(torrent)
        return
    source = torrent["info"]["source"]
    logger.info("unconfigured source: {}, {} by default".format(source, CONFIG["filter"]["default_behavior"]))
    if CONFIG["filter"]["default_behavior"] == "accept":
        handle_accept(torrent)

def handle_gz(*, torrent, api_response, fl_url):    
    tinfo = dict()
    # update info from torrent
    tinfo["tid"] = common.get_params_from_url(torrent["comment"])["torrentid"]
    tinfo["size"] = sum([f["length"] for f in torrent["info"]["files"]])
    tinfo["hash"] = common.get_info_hash(torrent)
    # update info from api_response
    if api_response is not None:
        api_tinfo = api_response["response"]["torrent"]
        tinfo["uploader"] = api_tinfo["username"]
        tinfo["media"] = api_tinfo["media"]
        tinfo["file_format"] = api_tinfo["format"]
    site = common.get_torrent_site(torrent)
    _handle(
        torrent=torrent,
        tinfo=tinfo,
        filter=configured_sites[site]["filter"],
        token_thresh=CONFIG[site]["token_thresh"],
        fl_url=fl_url,
    )

def handle_file(filepath):
    with open(filepath, "rb") as f:
        raw = f.read()
    torrent = bencode.decode(raw)
    site = common.get_torrent_site(torrent)
    logger.info("new torrent from {}: {}".format(site, filepath))
    if site not in configured_sites.keys():
        handle_default(torrent=torrent)
        return
    if args.skip_api:
        api_response = None
        fl_url = None
    else:        
        tid = common.get_params_from_url(torrent["comment"])["torrentid"]
        api = configured_sites[site]["api"]
        api_response = api.query_tid(tid)
        if api_response["status"] != "success":
            logger.info("error in response: {}".format(repr(api_response)))
            api_response = None
        fl_url = api.get_fl_url(tid)
    handle_gz(
        torrent=torrent,
        api_response=api_response,
        fl_url=fl_url,
    )

def handle_url(dl_url):
    def _call_api(api, tid):
        logger.info("calling api: {} tid: {}".format(api.apiname, tid))
        api_response = api.query_tid(tid)
        logger.info("api responded")
        return api_response
    def _download_torrent(dl_url):
        logger.info("downloading torrent_file")
        r = requests.get(dl_url, timeout=CONFIG["requests_timeout"], headers=download_headers)
        torrent = bencode.decode(r.content)
        logger.info("torrent file downloaded")
        return torrent    
    site = common.get_url_site(dl_url)
    logger.info("new torrent from {}: {}".format(site, dl_url))
    if site not in configured_sites:
        torrent = _download_torrent(dl_url)        
        handle_default(torrent)
        return
    tid = common.get_params_from_url(dl_url)["id"]
    api = configured_sites[site]["api"]
    pool = ThreadPool(processes=2)
    t_dl = pool.apply_async(_download_torrent, args=(dl_url,))
    if not args.skip_api:
        t_api = pool.apply_async(_call_api, args=(api, tid))
    pool.close()
    pool.join()
    if not args.skip_api:
        api_response = t_api.get()
    else:
        api_response = None
    handle_gz(
        torrent=t_dl.get(),
        api_response=api_response,
        fl_url=api.get_fl_url(tid),
    )

def check_dir():
    flist = os.listdir(CONFIG["filter"]["source_dir"])
    if len(flist) == 0:
        return
    for fname in flist:
        tpath = os.path.join(CONFIG["filter"]["source_dir"], fname)
        if os.path.splitext(fname)[1] == ".torrent":            
            handle_file(tpath)
            os.remove(tpath)
    common.flush_logger()

if args.url is not None:
    handle_url(args.url)
elif args.file is not None:
    handle_file(args.file)
else:
    # 持续监控文件夹
    logger.info("monitoring torrent files in {}".format(CONFIG["filter"]["source_dir"]))
    cnt = 0
    while True:
        try:
            check_dir()
        except KeyboardInterrupt:
            logger.info(traceback.format_exc())
            exit(0)
        except:
            logger.info(traceback.format_exc())
            pass
        time.sleep(0.2)
        if cnt % 300 == 0 and not args.no_tick:
            # 每分钟输出点东西，缓解黑屏焦虑
            logger.info("tick")
            common.flush_logger()
        cnt += 1