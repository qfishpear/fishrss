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

FISH_HEADERS = requests.utils.default_headers()
FISH_HEADERS['User-Agent'] = "FishRSS"

class GazelleApi(object):

    def __init__(self, *, 
        logger:logging.Logger,
        apiname,
        timer,
        api_url,
        authkey,
        torrent_pass,
        cache_dir=None,
        cookies=None,
        headers=None,
        timeout=10,
        skip_login=False,
        # discard
        **kwargs
    ):
        self.logger = logger
        self.apiname = apiname
        self.cache_dir = cache_dir
        self.cookies = cookies
        if headers is None:
            headers = requests.utils.default_headers()
        self.headers = headers
        self.timer = timer
        self.timeout = timeout
        self.api_url = api_url
        self.authkey = authkey
        self.torrent_pass = torrent_pass

        # limit the max retry to 1 to prohibit retrying from influencing the frequency control
        self.sess = requests.Session()
        self.sess.mount('https://', requests.adapters.HTTPAdapter(max_retries=1))
        self.sess.mount('http://', requests.adapters.HTTPAdapter(max_retries=1))

        # sanity check
        if cache_dir is not None:
            assert os.path.exists(cache_dir), "{}的api_cache_dir文件夹不存在：{}".format(apiname, cache_dir)
        else:
            self.logger.warning("{}未配置api cache dir".format(apiname))

        # try login
        if not skip_login:
            self.login()

    def login(self):
        js = self._query(params={"action":"index"}, use_cache=False)
        if js["status"] == "failure":
            if "error" in js.keys() and js["error"] == "bad credentials":
                self.logger.error("{}的鉴权凭证(cookie/apikey)填写不正确: {}".format(
                    self.apiname, repr(js)))
                assert js["error"] != "bad credential"
        if js["status"] != "success":
            self.logger.error("{}鉴权错误：{}".format(self.apiname, repr(js)))
            assert js["status"] == "success"
        uinfo = js["response"]
        self.username = uinfo["username"]
        self.uid = uinfo["id"]
        if self.authkey != uinfo["authkey"]:
            self.logger.warning("{}的authkey填写错误或过期，应当为(authkey should be) \"{}\"，而不是(but not) \"{}\"。"
                                "如果只是过期，则这不一定会导致错误，"
                                "但如果发现脚本运行不正常（比如token无法正常使用）请按照提示修改。".format(
                                self.apiname, uinfo["authkey"], self.authkey))
        if self.torrent_pass != uinfo["passkey"]:
            self.logger.error("{}的torrent_pass填写错误，应当为(torrent_pass should be) \"{}\"，而不是(but not) \"{}\"".format(
                                self.apiname, uinfo["passkey"], self.torrent_pass))
            assert self.torrent_pass == uinfo["passkey"]
        self.logger.info("{} logged in successfully, username：{} uid: {}".format(self.apiname, self.username, self.uid))        

    """
    此函数仅保证返回是一个dict，且至少含有"status"一个key
    """
    def _query(self, params: dict, use_cache=True) -> dict:
        if self.cache_dir is not None and use_cache:
            fname = "{}.json".format(urllib.parse.urlencode(params).replace("&", "_"))
            cache_file = os.path.join(self.cache_dir, fname)
            if os.path.exists(cache_file):
                with open(cache_file, "r") as f:
                    return json.load(f)
        self.logger.info("{} querying {}".format(self.apiname, urllib.parse.urlencode(params)))
        self.timer.wait()
        r = self.sess.get(
            url=self.api_url, 
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
            return {"status": "json decode failure", "raw_response":r.text}        
        if js["status"] == "failure":
            if "error" in js.keys() and js["error"] == "bad credentials":
                self.logger.warning("login credentials (cookie/apikey) of {} is wrong: {}".format(
                    self.apiname, repr(js)))
                # 鉴权错误时直接返回结果不保存至cache
                return js
        if self.cache_dir is not None and use_cache:
            with open(cache_file, "w") as f:
                json.dump(js, f)
        return js

    def query_hash(self, h, **kwargs):
        return self._query(params={
            "action": "torrent",
            "hash": h.upper(),
        }, **kwargs)

    def query_tid(self, tid, **kwargs):
        return self._query(params={
            "action": "torrent",
            "id": tid,
        }, **kwargs)
    
    def query_gid(self, gid, **kwargs):
        return self._query(params={
            "action": "torrentgroup",
            "id": gid,
        }, **kwargs)

    def query_uploaded(self, uid, **kwargs):
        return self._query(params={
            "action":"user_torrents",
            "id":uid,
            "type":"uploaded",
        })

    def search(self, search_params : dict, **kwargs):
        params = search_params.copy()
        params["action"] = "browse"
        return self._query(params=params, **kwargs)

    def search_torrent_by_filename(self, filename, **kwargs):
        def _escape(s):
            """
            replace characters to space except alphabet and numbers
            """
            s2 = ""
            for ch in s:
                if ch.isalnum():
                    s2 += ch
                else:
                    s2 += " "
            s = s2
            while s.replace("  ", " ") != s:
                s = s.replace("  ", " ")
            return s
        return self.search(search_params={
            # 由于煞笔的按文件名搜索功能有毒，搜文件名时把文件名中非字母数字的部分全部去掉
            "filelist":_escape(filename),
        }, **kwargs)

    def get_dl_url(self, tid):
        raise NotImplementedError

    def get_fl_url(self, tid):
        return self.get_dl_url(tid) + "&usetoken=1"

class REDApi(GazelleApi):

    def __init__(self, *, apikey=None, **kwargs):
        headers = FISH_HEADERS.copy()
        self.apikey = apikey
        if apikey is not None:
            timer = Timer(10, 10.5)
            headers["Authorization"] = apikey
        else:
            timer = Timer(5, 10.5)
        super().__init__(
            apiname="red",
            headers=headers,
            timer=timer, 
            api_url="https://redacted.ch/ajax.php",
            **kwargs
        )

    def get_dl_url(self, tid):
        return "https://redacted.ch/torrents.php?action=download&id={}&authkey={}&torrent_pass={}".format(
            tid, self.authkey, self.torrent_pass)
    
    # override fl link for RED to abide the rule
    def get_fl_url(self, tid):
        raise NotImplementedError

class DICApi(GazelleApi):

    def __init__(self, **kwargs):
        super().__init__(
            apiname="dic",
            headers=FISH_HEADERS,
            timer=Timer(5, 10.5),
            api_url="https://dicmusic.club/ajax.php",
            **kwargs
        )

    def get_dl_url(self, tid):
        return "https://dicmusic.club/torrents.php?action=download&id={}&authkey={}&torrent_pass={}".format(
            tid, self.authkey, self.torrent_pass)

class SnakeApi(GazelleApi):

    def __init__(self, **kwargs):
        super().__init__(
            apiname="snake",
            headers=FISH_HEADERS,
            timer=Timer(5, 10.5),
            api_url="https://snakepop.art/ajax.php",
            **kwargs
        )

    def get_dl_url(self, tid):
        return "https://snakepop.art/torrents.php?action=download&id={}&authkey={}&torrent_pass={}".format(
            tid, self.authkey, self.torrent_pass)

class OPSApi(GazelleApi):

    def __init__(self, *, apikey=None, **kwargs):
        headers = FISH_HEADERS.copy()
        self.apikey = apikey
        if apikey is not None:
            headers["Authorization"] = apikey
        super().__init__(
            apiname="ops",
            headers=headers,
            timer=Timer(5, 10.5),
            api_url="https://orpheus.network/ajax.php",
            **kwargs
        )

    def get_dl_url(self, tid):
        return "https://orpheus.network/torrents.php?action=download&id={}&torrent_pass={}".format(
            tid, self.torrent_pass)

    # override fl link for OPS to abide the rule
    def get_fl_url(self, tid):
        raise NotImplementedError