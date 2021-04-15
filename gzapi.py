import time
import os
import requests
import json
import urllib
import traceback
import logging
"""
所有api参数中的
tid表示torrentid种子id
gid表示groupid种子组id，也即种子链接中id=后面的那个id
uid表示账号id
"""

# 提供一个计时器，每次wait会等待直到前count次wait之后的interval秒
class Timer(object):

    def __init__(self, count, interval):
        self.history = [0 for _ in range(count)]
        self.interval = interval

    def wait(self):
        t = time.time()
        if t - self.history[0] < self.interval:
            time.sleep(self.interval - (t - self.history[0]) + 0.1)
            t = time.time()
        self.history = self.history[1:] + [t,]

class GazelleApi(object):

    def __init__(self, *, 
        logger:logging.Logger,
        apiname,
        timer,
        cache_dir=None,
        cookies=None,
        headers=None,
        timeout=10,
    ):
        self.logger = logger
        self.apiname = apiname
        self.cache_dir = cache_dir
        self.cookies = cookies
        self.headers = headers
        self.timer = timer
        self.timeout = timeout        
        # sanity check
        if cache_dir is not None:
            assert os.path.exists(cache_dir), "{}的api cache dir文件夹不存在：{}".format(apiname, cache_dir)
        else:
            self.logger.warning("{}未配置api cache dir".format(apiname))

    """
    此函数仅保证返回是一个dict，且至少含有"status"一个key
    """
    def _query(self, url: str, params: dict, use_cache=True) -> dict:
        if self.cache_dir != None and use_cache:
            fname = "{}.json".format(urllib.parse.urlencode(params).replace("&", "_"))
            cache_file = os.path.join(self.cache_dir, fname)
            if os.path.exists(cache_file):
                with open(cache_file, "r") as f:
                    return json.load(f)
        self.logger.info("{} querying {}".format(self.apiname, urllib.parse.urlencode(params)))
        self.timer.wait()
        r = requests.get(
            url=url, 
            cookies=self.cookies,
            headers=self.headers,
            params=params,
            timeout=self.timeout
        )
        try:
            js = json.loads(r.text)
        except json.JSONDecodeError:
            self.logger.info(r.text)
            self.logger.info(traceback.format_exc())
            return {"status": "json decode failure"}
        if self.cache_dir != None and use_cache:
            with open(cache_file, "w") as f:
                json.dump(js, f)
        return js


class REDApi(GazelleApi):

    def __init__(self, *, authkey, torrent_pass, apikey=None, **kwargs):
        headers = requests.utils.default_headers()
        if apikey is not None:
            timer = Timer(10, 10.5)
            headers["Authorization"] = apikey
        else:
            timer = Timer(5, 10.5)
        self.authkey = authkey
        self.torrent_pass = torrent_pass
        super().__init__(apiname="red", headers=headers, timer=timer, **kwargs)

    def query(self, params, **kwargs):
        return super()._query(url="https://redacted.ch/ajax.php", params=params, **kwargs)

    def query_hash(self, h, **kwargs):
        return self.query(params={
            "action": "torrent",
            "hash": h.upper(),
        }, **kwargs)

    def query_tid(self, tid, **kwargs):
        return self.query(params={
            "action": "torrent",
            "id": tid,
        }, **kwargs)
    
    def query_gid(self, gid, **kwargs):
        return self.query(params={
            "action": "torrentgroup", 
            "id": gid,
        }, **kwargs)

    def get_dl_url(self, tid):
        return "https://redacted.ch/torrents.php?action=download&id={}&authkey={}&torrent_pass={}".format(
            tid, self.authkey, self.torrent_pass)
    
    def get_fl_url(self, tid):
        return self.get_dl_url(tid) + "&usetoken=1"

class DICApi(GazelleApi):

    def __init__(self, *, authkey, torrent_pass, apikey=None, **kwargs):
        self.authkey = authkey
        self.torrent_pass = torrent_pass
        super().__init__(apiname="dic", timer=Timer(5, 10.5), **kwargs)

    def query(self, params, **kwargs):
        return super()._query(url="https://dicmusic.club/ajax.php", params=params, **kwargs)

    def query_hash(self, h, **kwargs):
        return self.query(params={
            "action": "torrent",
            "hash": h.upper(),
        }, **kwargs)

    def query_tid(self, tid, **kwargs):
        return self.query(params={
            "action": "torrent",
            "id": tid,
        }, **kwargs)

    def query_uploaded(self, uid, **kwargs):
        return self.query(params={
            "action":"user_torrents",
            "id":50065,
            "type":"uploaded",
        })

    def get_dl_url(self, tid):
        return "https://dicmusic.club/torrents.php?action=download&id={}&authkey={}&torrent_pass={}".format(
            tid, self.authkey, self.torrent_pass)

    def get_fl_url(self, tid):
        return self.get_dl_url(tid) + "&usetoken=1"
