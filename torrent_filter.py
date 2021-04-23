import logging
import os
class TorrentFilter(object):

    FILTER_CONFIG_TEMPLATE = {
        "name": "redfilter",
        "banlist" : "/home7/fishpear/rss/ban_red.txt",
        "whitelist" : "/home7/fishpear/rss/white_red.txt",
        "media" : set(["CD", "Vinyl", "WEB"]),
        "format": set(["FLAC", "WAV"]),
        "sizelim": (100 * 1024**2, 1024**3),
    }

    def __init__(self, config, logger:logging.Logger):
        self.config = config
        self.logger = logger
        #sanity check
        for key in set(TorrentFilter.FILTER_CONFIG_TEMPLATE.keys()) - set(config.keys()):
            assert False, "filter_config配置错误：缺少{}".format(key)
        for key in set(config.keys()) - set(TorrentFilter.FILTER_CONFIG_TEMPLATE.keys()):
            assert False, "filter_config配置错误：多余的配置项{}".format(key)
        if config["banlist"] is not None:
            assert os.path.exists(config["banlist"]), "filter_config配置错误：被ban用户列表文件{}不存在".format(config["banlist"])
        assert config["media"] is None or type(config["media"]) is set, \
            "filter_config配置错误：媒体类型(media)应当是集合或者None，而不是{}".format(repr(config["media"]))
        assert config["format"] is None or type(config["format"]) is set, \
            "filter_config配置错误：格式类型(format)应当是集合或者None，而不是{}".format(repr(config["media"]))
        if config["sizelim"] is not None:
            assert type(config["sizelim"]) is tuple and len(config["sizelim"]) == 2, \
                "filter_config配置错误：体积范围(sizelim)应当是一个二元组(x,y)或者None，而不是{}".format(repr(config["sizelim"]))
    
    def check_tinfo(self, *,
        uploader=None,
        media=None,
        file_format=None,
        size=None,
        tid=None,
        # discarded:
        **kwargs
    ):
        self.logger.info("{}: checking".format(self.config["name"]))
        self.logger.info("tid: {} uploader: {} media: {} format: {} size: {:.1f}MB".format(
            tid, uploader, media, file_format, size / 1024**2,
        ))
        if self.config["whitelist"] is not None:
            with open(self.config["whitelist"], "r") as f:
                whitelisted_users = set([line.strip() for line in f])
            if uploader in whitelisted_users:
                self.logger.info("whitelisted uploader: {}".format(uploader))
                return "accept"
        if self.config["banlist"] is not None:
            with open(self.config["banlist"], "r") as f:
                bannedusers = set([line.strip() for line in f])
            if uploader in bannedusers:
                return "banned user"
        if self.config["media"] is not None:
            if media not in self.config["media"]:
                return "wrong media"
        if self.config["format"] is not None:
            if file_format not in self.config["format"]:
                return "wrong format"
        if self.config["sizelim"] is not None:
            if size < self.config["sizelim"][0]:
                return "size too small"
            if size > self.config["sizelim"][1]:
                return "size too big"
        return "accept"


    def check_json_response(self, js: dict):
        self.logger.info("{}: checking".format(self.config["name"]))
        if js["status"] != "success":
            return "error status: {}".format(js["status"])
        tinfo = js["response"]["torrent"]
        return self.check_tinfo(
            uploader=tinfo["username"],
            media=tinfo["media"],
            file_format=tinfo["format"],
            size=tinfo["size"],
            tid=tinfo["id"],
        )