import requests
import json
import time
import os, sys
import logging
import traceback
import bencode
import hashlib
import urllib
import collections
import base64
import argparse
from IPython import embed

from config import CONFIG
import common
from common import logger
import gzapi

IGNORED_PATH =[
    "@eaDir", #dummy directory created by Synology
    ".DS_Store", #dummy directory created by macOS
]

def check_path(path, is_file=False, auto_create=False):
    if path is not None:
        abspath = os.path.abspath(path)
        if os.path.exists(abspath):
            if is_file and not os.path.isfile(abspath):
                logger.warning("path {} must be a file".format(path))
                exit(0)
            if not is_file and not os.path.isdir(abspath):
                logger.warning("path {} must be a folder".format(path))
                exit(0)
        else:
            if not auto_create:
                logger.warning("path doesn't exist: {} ".format(path))
                exit(0)
            else:
                if is_file:
                    logger.info("file automatically created: {}".format(path))
                    folder = os.path.split(abspath)[0]
                    if not os.path.exists(folder):
                        os.makedirs(folder)
                    with open(abspath, "w") as _:
                        pass
                else:
                    logger.info("directory automatically created: {}".format(path))
                    os.makedirs(path)

parser = argparse.ArgumentParser(description="""
功能：扫描指定文件夹进行辅种 scan a directory to find torrents that can be cross-seeded on given tracker
""")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--dir', default=None, help="批量辅种的文件夹 folder for batch cross-seeding")
group.add_argument('--single-dir', default=None, help="单个辅种的文件夹 folder for just one cross-seeding")
parser.add_argument('--site', required=True, choices=common.SITE_CONST.keys(),
                    help="扫描的站点 the tracker to scan for cross-seeding.")
parser.add_argument('--result-dir', required=True, 
                    help="储存扫描结果的文件夹 folder for saving scanned results")
parser.add_argument('--api-frequency', default=None,
                    help="if set, override the default api calling frequency. Unit: number of api call per 10 seconds (must be integer)")
parser.add_argument("--no-download", action="store_true", default=False,
                    help="if set, don't download the .torrent files. Only the id of torrents are saved")
if len(sys.argv) == 1:
    parser.print_help()
    exit(0)
args = parser.parse_args()

# check and create files/folders

# basic folders
check_path(args.dir)
check_path(args.single_dir)
check_path(args.result_dir)

# scanned directories, one absolute path per line
scan_history_path = os.path.join(args.result_dir, "scan_history.txt")
check_path(scan_history_path, is_file=True, auto_create=True)

# scanned results, one torrent url per line
result_url_path = os.path.join(args.result_dir, "result_url.txt")
check_path(result_url_path, is_file=True, auto_create=True)

# mapping of scanning results, "{path}\t{result}" for each line
result_map_path = os.path.join(args.result_dir, "result_mapping.txt")
check_path(result_map_path, is_file=True, auto_create=True)

# folder of downloaded .torrents files of scanning results
result_torrent_path = os.path.join(args.result_dir, "torrents/")
check_path(result_torrent_path, is_file=False, auto_create=True)

# urls of .torrents files that are unable to download, one torrent url per line
result_url_undownloaded_path = os.path.join(args.result_dir, "result_url_undownloaded.txt")
check_path(result_url_undownloaded_path, is_file=True, auto_create=True)

GLOBAL = dict()
GLOBAL["found"] = 0
GLOBAL["downloaded"] = 0
GLOBAL["scanned"] = 0
GLOBAL["cnt_dl_fail"] = 0

def work(folder, api):
    GLOBAL["scanned"] += 1

    tsize = 0
    flist = []
    for path, _, files in os.walk(folder):
        is_ignored = False
        for ignore_str in IGNORED_PATH:
            if ignore_str in path:
                is_ignored = True
        if not is_ignored:
            tsize += sum([os.path.getsize(os.path.join(path, name)) for name in files])
            flist += files
    flist.sort(key=lambda fname:-len(fname))

    tid = -1
    # search for the files with top 10 longest name 
    for fname in flist[:5]:
        resp = api.search_torrent_by_filename(fname, use_cache=False)
        if resp["status"] != "success":
            logger.info("api failure: {}".format(repr(resp)))
            continue
        torrents = sum([group["torrents"] for group in resp["response"]["results"] if "torrents" in group.keys()], [])
        for t in torrents:
            if t["size"] == tsize:
                tid = t["torrentId"]
                break
        if tid != -1:
            break
        # if it is impossible to find a match, just stop:
        if len(torrents) == 0 or resp["response"]["pages"] <= 1:
            break

    if tid == -1:
        logger.info("not found")
        with open(scan_history_path, "a") as f:
            f.write("{}\n".format(folder))
        with open(result_map_path, "a") as f:
            f.write("{}\t{}\n".format(os.path.split(folder)[1], tid))
        downloaded = False
    else:
        GLOBAL["found"] += 1
        logger.info("found, torrentid={}".format(tid))
        dl_url = api.get_dl_url(tid)
        downloaded = False
        if not args.no_download:
            try:
                resp = requests.get(dl_url, headers=gzapi.FISH_HEADERS, timeout=CONFIG["requests_timeout"])
                # check the integrity of torrent
                _ = bencode.decode(resp.content)
                # assert common.get_info_hash(torrent) == 
                # use the folder's name as the torrent's name to help crossseeding
                tpath = os.path.join(result_torrent_path, "{}.torrent".format(os.path.split(folder)[1]))
                logger.info("saving to {}".format(tpath))
                with open(tpath, "wb") as f:
                    f.write(resp.content)
                downloaded = True
                GLOBAL["downloaded"] += 1
            except:
                logger.info("fail to download .torrent file from {}".format(dl_url))
                GLOBAL["cnt_dl_fail"] += 1
                if GLOBAL["cnt_dl_fail"] <= 10:
                    logger.info(traceback.format_exc())
                    logger.info("It might because the torrent id {} has reached the "
                                "limitation of non-browser downloading of {}. "
                                "The URL of failed downloading will be saved to {}. "
                                "You can download it from your own browser.".format(
                                    tid, args.site, result_url_undownloaded_path))
                    logger.info("下载种子(id {})失败，这可能是因为触发了{}对于非浏览器下载该种子的限制。"
                                "失败种子的下载链接保存在{}里，你可以用你的浏览器从该链接下载种子".format(
                            tid, args.site, result_url_undownloaded_path))
                    if GLOBAL["cnt_dl_fail"] == 10:
                        logger.info("suppress further hinting for .torrent file downloading failure")
        with open(result_url_path, "a") as f:
            f.write("{}\n".format(dl_url))
        with open(result_map_path, "a") as f:
            f.write("{}\t{}\n".format(os.path.split(folder)[1], tid))
        if not downloaded:
            with open(result_url_undownloaded_path, "a") as f:
                f.write("{}\n".format(dl_url))
        with open(scan_history_path, "a") as f:
            f.write("{}\n".format(folder))
    return tid, downloaded
api = common.get_api(args.site)
if args.api_frequency is not None:
    api.timer = gzapi.Timer(args.api_frequency, 10.5)

if args.single_dir:
    folder = os.path.abspath(args.single_dir)
    logger.info("scanning {} for cross seeding in {}".format(
        folder, args.site))
    tid, downloaded = work(folder, api)
else:
    try:
        with open(scan_history_path, "r") as f:
            scanned_folders_set = set([line.strip() for line in f])
        candidates = []
        parent_folder = os.path.abspath(args.dir)
        for f in os.listdir(parent_folder):
            path = os.path.join(parent_folder, f)
            if os.path.isdir(path):
                candidates.append(path)
        unscanned_folders = [path for path in candidates if path not in scanned_folders_set]
        logger.info("{}/{} unscanned folders found in {}, start scanning for cross-seeding {}".format(
            len(unscanned_folders), len(candidates), args.dir, args.site))
        for i, folder in enumerate(unscanned_folders):
            logger.info("{}/{} {}".format(i+1, len(unscanned_folders), folder))
            work(folder, api)
    except KeyboardInterrupt:
        logger.info(traceback.format_exc())
        logger.info("{} folders scanned, {} torrents found, {} .torrent file downloaded to {}".format(
            GLOBAL["scanned"], GLOBAL["found"], GLOBAL["downloaded"], args.site
        ))
        exit(0)
    except Exception as _:
        logger.info(traceback.format_exc())
        pass