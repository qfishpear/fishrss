import os
from common import get_api, get_filter, logger, SITE_CONST
from config import CONFIG
import traceback

def check_path(path, name):
    if path is not None:
        if not os.path.exists(path):
            logger.info("{}不存在，请创建:{}".format(name, path))

# 其他
check_path(CONFIG["filter"]["source_dir"], "source_dir")
check_path(CONFIG["filter"]["dest_dir"], "dest_dir")
# 网站
configured_sites = {}
for site in SITE_CONST.keys():
    if site not in CONFIG.keys():
        logger.info("{}未配置".format(site))
    else:
        check_path(CONFIG[site]["filter_config"]["banlist"], "{}的banlist".format(site))
        try:
            api = get_api(site)
        except:
            logger.info("{} fail to login".format(site))
            logger.info(traceback.format_exc())
        try:        
            f = get_filter(site)
        except:
            logger.info("error in {}'s filter_config".format(site))
            logger.info(traceback.format_exc())
# bt客户端
try:
    import deluge_client
    DELUGE = CONFIG["deluge"]
    de = deluge_client.DelugeRPCClient(DELUGE["ip"], DELUGE["port"], DELUGE["username"], DELUGE["password"])
    de.connect()
    assert(de.connected)
    logger.info("deluge is correctly configured")
except:
    logger.info("deluge配置错误无法连接")
    logger.info(traceback.format_exc())
