from common import get_api, get_filter, logger
from config import CONFIG
import traceback

for site in ["red", "dic"]:
    if site not in CONFIG:
        logger.info("{}未配置".format(site))
    else:
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