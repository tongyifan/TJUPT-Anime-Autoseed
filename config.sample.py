import os

# TJUPT的Cookies，格式为"key1=val1; key2=val2"
TJUPT_COOKIES_RAW = ""

# qBittorrent相关配置
QBITTORRENT_CONFIG = {
    "url": "http://127.0.0.1:8080/",
    "username": "username",
    "password": "password",
    "savepath": "savepath",
}

# RSS入口，rss.py会轮询这些入口
RSS_ENTRIES = [
    "https://api.rhilip.info/rss/dmhy.xml",
    "https://acg.rip/.xml",
    "https://bangumi.moe/rss/latest",
    "https://mikanani.me/RSS/Classic",
    "https://comicat.org/rss.xml",
]

KEYWORD_BLACKLIST = ["BDRip", "BDMV", "Blu-ray"]

# ServerChan，用于Error级信息的上报，见 http://sc.ftqq.com/3.version
SERVERCHAN_TOKEN = ""

PTGEN_ENDPOINTS = [
    "https://ptgen.tju.pt/infogen",
]

# -- 下面的不需要修改 --
base_path = os.path.dirname(__file__)
