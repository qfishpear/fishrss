import logging
import os
class TorrentFilter(object):

    FILTER_CONFIG_TEMPLATE = {
        "name": "redfilter",
        "banlist" : "/home7/fishpear/rss/ban_red.txt",
        "media" : set(["CD", "Vinyl", "WEB"]),
        "format": set(["FLAC", "WAV"]),
        "sizelim": (100 * 1024**2, 1024**3),
    }

    def __init__(self, config, logger:logging.Logger):
        self.config = config
        self.logger = logger
        #sanity check
        for key in set(TorrentFilter.FILTER_CONFIG_TEMPLATE.keys()) - set(config.keys()):
            assert False, "配置错误：缺少{}".format(key)
        for key in set(config.keys()) - set(TorrentFilter.FILTER_CONFIG_TEMPLATE.keys()):
            assert False, "配置错误：多于的配置项{}".format(key)
        if config["banlist"] is not None:
            assert os.path.exists(config["banlist"]), "配置错误：被ban用户列表文件{}不存在".format(config["banlist"])
        if config["media"] is not None:
            assert type(config["media"]) is set, "配置错误：媒体类型(media)应当是集合或者None"
        if config["media"] is not None:
            assert config["format"] is None or type(config["format"]) is set, \
                "配置错误：格式类型{}应当是集合或者None".format(config["media"])
        if config["sizelim"] is not None:
            assert type(config["sizelim"][0]) is int and type(config["sizelim"][1]) is int and \
                   0 < config["sizelim"][0] and config["sizelim"][0] < config["sizelim"][1],  \
                    "配置错误：体积范围[{},{}]应当是正整数区间".format(config["sizelim"][0], config["sizelim"][1])
    
    def check_json_response(self, js: dict):
        self.logger.info("{}: checking".format(self.config["name"]))
        if js["status"] != "success":
            return "error status: {}".format(js["status"])
        response = js["response"]
        tinfo = response["torrent"]
        ginfo = response["group"]
        self.logger.info("uploader: {} media: {} format: {} releasetype: {} size: {:.1f}MB".format(
            tinfo["username"],
            tinfo["media"],
            tinfo["format"],
            ginfo["releaseType"],
            tinfo["size"] / 1024**2,
        ))
        if self.config["banlist"] is not None:
            with open(self.config["banlist"], "r") as f:
                bannedusers = set([line.strip() for line in f])            
            if tinfo["username"] in bannedusers:
                return "banned user"
        if self.config["media"] is not None:
            if tinfo["media"] not in self.config["media"]:
                return "wrong media"
        if self.config["format"] is not None:
            if tinfo["format"] not in self.config["format"]:
                return "wrong format"
        if self.config["sizelim"] is not None:
            if tinfo["size"] < self.config["sizelim"][0]:
                return "size too small"
            if tinfo["size"] > self.config["sizelim"][1]:
                return "size too big"
        return "accept"

