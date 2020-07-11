import os

# TJUPT的Cookies，格式为"key1=val1; key2=val2"
TJUPT_COOKIES_RAW = ""

# qBittorrent相关配置
QBITTORRENT_CONFIG = {
    "url": "http://127.0.0.1:8080/",
    "username": "username",
    "password": "password"
}

# RSS入口，rss.py会轮询这些入口
RSS_ENTRIES = [
    "https://api.rhilip.info/rss/dmhy.xml",
    "https://acg.rip/.xml",
    "https://bangumi.moe/rss/latest",
    "https://mikanani.me/RSS/Classic"
]

# ServerChan，用于Error级信息的上报，见 http://sc.ftqq.com/3.version
SERVERCHAN_TOKEN = ""

# -- 下面的不需要修改 --
base_path = os.path.dirname(__file__)