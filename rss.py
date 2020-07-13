import hashlib
import io
import json
import os

import bencoder
import feedparser
import requests
from qbittorrent import Client

from config import RSS_ENTRIES, QBITTORRENT_CONFIG, base_path
from utils.configReader import read_configs
from utils.database import Database
from utils.logger import logger


class RSSReader:
    def __init__(self):
        self.configs = read_configs()
        self.qb = None
        self.db = None
        self.cache = {}
        if os.path.exists(os.path.join(base_path, 'instance/cache.json')):
            with open(os.path.join(base_path, "instance/cache.json"), 'r') as fp:
                self.cache = json.load(fp)

    def connect(self):
        if not self.qb:
            self.qb = Client(QBITTORRENT_CONFIG['url'])
            self.qb.login(QBITTORRENT_CONFIG['username'], QBITTORRENT_CONFIG['password'])

        if not self.db:
            self.db = Database()

    def read_rss(self):
        items = {}
        for entry in RSS_ENTRIES:
            d = feedparser.parse(entry)
            for item in d.entries:
                if item['title'] in items or item['title'] in self.cache:
                    continue

                if 'links' in item:
                    for link in item['links']:
                        if link['type'] == 'application/x-bittorrent' or '.torrent' in link['href']:
                            items[item['title']] = link['href']
                            break
                elif 'link' in item:
                    items[item['title']] = item['link']

        logger.info("从RSS中读取到%s个新资源", len(items))

        with open(os.path.join(base_path, "instance/cache.json"), 'w') as fp:
            json.dump({**items, **self.cache}, fp)

        for item in items:
            for config in self.configs:
                if all(k in item for k in self.configs[config]['keyword'].split(' ')):
                    logger.info("资源「%s」命中任务「%s」，推送至qB", item, config)
                    self.connect()
                    try:
                        resp = requests.get(items[item])
                    except requests.exceptions.RequestException as e:
                        logger.error("种子文件下载失败，资源「%s」，地址「%s」，错误「%s」", item, items[item], repr(e))
                        break
                    if resp.status_code != 200:
                        logger.error("种子文件下载失败，资源「%s」，地址「%s」，错误「%s」", item, items[item], resp.status_code)
                        break

                    torrent = resp.content

                    try:
                        info = bencoder.decode(torrent)[b'info']
                        info_hash = hashlib.sha1(bencoder.encode(info)).hexdigest()
                    except AssertionError:
                        logger.error("解析种子错误，资源「%s」，地址「%s」", item, items[item])
                        break

                    added = self.db.insert_task(str(self.configs[config]['id']), info_hash)  # 如果插入任务失败，added=False
                    if added:  # 如果添加任务成功，将种子文件丢到qb，并存储到torrents文件夹备用
                        self.qb.download_from_file(torrent)
                        with open(os.path.join(base_path, "torrents/{}.torrent".format(info_hash)), 'wb') as fp:
                            fp.write(torrent)

                    break  # 不再继续匹配其他配置项


if __name__ == '__main__':
    rr = RSSReader()
    rr.read_rss()
