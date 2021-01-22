import base64
import hashlib
import json
import os
import time
import urllib
from argparse import ArgumentParser
from datetime import datetime
from urllib.parse import urlencode

import bencoder
import feedparser
import requests
from qbittorrent import Client

from config import RSS_ENTRIES, QBITTORRENT_CONFIG, base_path
from utils.configReader import read_configs
from utils.database import Database
from utils.logger import logger


class RSSReader:
    def __init__(self, mode, config_id=None):
        self.mode = mode
        self.cache = {}
        if self.mode != "rss":
            if config_id is None:
                logger.error("使用search模式时必须传入config_id")
                exit()
            self.configs = read_configs(
                os.path.join(base_path, f"instance/configs/{config_id}.yaml")
            )
        else:
            self.configs = read_configs()
            if os.path.exists(os.path.join(base_path, "instance/cache.json")):
                with open(os.path.join(base_path, "instance/cache.json"), "r") as fp:
                    try:
                        self.cache = json.load(fp)
                    except json.decoder.JSONDecodeError:
                        os.remove(os.path.join(base_path, "instance/cache.json"))
        self.qb = None
        self.db = None

    def connect(self):
        if not self.qb:
            self.qb = Client(QBITTORRENT_CONFIG["url"])
            self.qb.login(
                QBITTORRENT_CONFIG["username"], QBITTORRENT_CONFIG["password"]
            )

        if not self.db:
            self.db = Database()

    def read_rss(self):
        items = {}
        this_rss_entries = (
            RSS_ENTRIES if self.mode == "rss" else self.generate_entries()
        )
        for entry in this_rss_entries:
            d = feedparser.parse(entry)
            for item in d.entries:
                if item["title"] in items or item["title"] in self.cache:
                    continue

                published_timestamp = (
                    time.mktime(item["published_parsed"]) - time.timezone
                )
                if time.time() - published_timestamp > 30 * 24 * 60 * 60:  # 跳过超过了30天的资源
                    continue

                if "links" in item:
                    for link in item["links"]:
                        if (
                            link["type"] == "application/x-bittorrent"
                            or ".torrent" in link["href"]
                        ):
                            if "magnet" in link["href"]:
                                hex_info_hash = base64.b32decode(
                                    link["href"].lstrip("magnet:?xt=urn:btih:")[:32]
                                ).hex()

                                items[
                                    item["title"]
                                ] = f"https://dl.dmhy.org/{datetime.fromtimestamp(published_timestamp).strftime('%Y/%m/%d')}/{hex_info_hash}.torrent"
                            else:
                                items[item["title"]] = link["href"]
                            break
                elif "link" in item:
                    items[item["title"]] = item["link"]

        logger.info("从RSS中读取到%s个新资源", len(items))

        with open(os.path.join(base_path, "instance/cache.json"), "w") as fp:
            json.dump({**items, **self.cache}, fp)

        for item in items:
            for config in self.configs:
                if all(k in item for k in self.configs[config]["keyword"].split(" ")):
                    logger.info("资源「%s」命中任务「%s」，推送至qB", item, config)
                    self.connect()
                    try:
                        resp = requests.get(items[item])
                    except requests.exceptions.RequestException as e:
                        logger.error(
                            "种子文件下载失败，资源「%s」，地址「%s」，错误「%s」", item, items[item], repr(e)
                        )
                        break
                    if resp.status_code != 200:
                        logger.error(
                            "种子文件下载失败，资源「%s」，地址「%s」，错误「%s」",
                            item,
                            items[item],
                            resp.status_code,
                        )
                        break

                    torrent = resp.content

                    try:
                        info = bencoder.decode(torrent)[b"info"]
                        info_hash = hashlib.sha1(bencoder.encode(info)).hexdigest()
                    except AssertionError:
                        logger.error("解析种子错误，资源「%s」，地址「%s」", item, items[item])
                        break

                    added = self.db.insert_task(
                        str(self.configs[config]["id"]), info_hash
                    )  # 如果插入任务失败，added=False
                    if added:  # 如果添加任务成功，将种子文件丢到qb，并存储到torrents文件夹备用
                        self.qb.download_from_file(
                            torrent, savepath=QBITTORRENT_CONFIG["savepath"]
                        )
                        with open(
                            os.path.join(
                                base_path, "torrents/{}.torrent".format(info_hash)
                            ),
                            "wb",
                        ) as fp:
                            fp.write(torrent)

                    break  # 不再继续匹配其他配置项

    def generate_entries(self):
        entries = []
        for config in self.configs:
            keyword = urlencode({"keyword": self.configs[config]["keyword"]})
            entries.append(f"https://share.dmhy.org/topics/rss/rss.xml?{keyword}")

        return entries


if __name__ == "__main__":
    parse = ArgumentParser()
    parse.add_argument(
        "-m",
        "--mode",
        help="rss为常规更新模式，search为通过搜索添加任务模式",
        dest="mode",
        choices=["rss", "search"],
        default="rss",
    )
    parse.add_argument(
        "-c",
        "--config_id",
        help="rss为常规更新模式，search为通过搜索添加任务模式",
        dest="config_id",
        default=None,
    )
    argv = parse.parse_args()

    rr = RSSReader(argv.mode, argv.config_id)
    rr.read_rss()
