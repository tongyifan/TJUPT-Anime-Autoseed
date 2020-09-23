import logging
import os
from logging.handlers import RotatingFileHandler, HTTPHandler

from config import base_path, SERVERCHAN_TOKEN

instance_log_file = os.path.join(base_path, "logs/autoseed.log")

logging_datefmt = "%m/%d/%Y %I:%M:%S %p"
logging_format = "%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"

logFormatter = logging.Formatter(fmt=logging_format, datefmt=logging_datefmt)

logger = logging.getLogger()
logger.setLevel(logging.NOTSET)
while (
    logger.handlers
):  # Remove un-format logging in Stream, or all of messages are appearing more than once.
    logger.handlers.pop()

if instance_log_file:
    fileHandler = RotatingFileHandler(
        filename=instance_log_file, mode="a", maxBytes=5 * 1024 * 1024, backupCount=2
    )
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

if SERVERCHAN_TOKEN:

    class ServerChanHandler(HTTPHandler):
        def __init__(self, serverchan_token: str):
            logging.Handler.__init__(self)
            self.token = serverchan_token

        def emit(self, record: logging.LogRecord) -> None:
            if record.levelno >= logging.ERROR:
                try:
                    import requests

                    requests.post(
                        "https://sc.ftqq.com/{}.send".format(self.token),
                        data={"text": "发种姬出错啦！", "desp": self.format(record)},
                    )
                except Exception:
                    self.handleError(record)

    serverChanHandler = ServerChanHandler(SERVERCHAN_TOKEN)
    serverChanHandler.setFormatter(logFormatter)
    logger.addHandler(serverChanHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("feedparser").setLevel(logging.WARNING)
logging.getLogger("qbittorrent").setLevel(logging.WARNING)
