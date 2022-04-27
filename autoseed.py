import os
import re
import traceback
import uuid
from argparse import ArgumentParser
from http.cookies import SimpleCookie
from typing import Union

import bencoder
import requests
from qbittorrent import Client

from config import QBITTORRENT_CONFIG, base_path, TJUPT_COOKIES_RAW, PTGEN_ENDPOINTS
from utils.configReader import read_configs
from utils.database import Database
from utils.logger import logger
from utils.pattern import pattern_group


def parse_cookies(cookies_raw: str) -> dict:
    return {key: morsel.value for key, morsel in SimpleCookie(cookies_raw).items()}


class Autoseed:
    qb: Client = None
    db: Database = None

    info_hash: str = None
    torrent: dict = None
    torrent_name: str = None
    torrent_path: str = None

    config_id: Union[int, str, uuid.UUID] = None
    config: dict = None

    def run(self, info_hash, config_id=None):
        self.info_hash = info_hash
        self.config_id = config_id
        self.check_task_valid()

        torrent_info = self.format_torrent_info()
        self.post_to_site(torrent_info)

    def _connect(self, skip_qb=False):
        if not skip_qb and not self.qb:
            try:
                self.qb = Client(QBITTORRENT_CONFIG["url"])
                self.qb.login(
                    QBITTORRENT_CONFIG["username"], QBITTORRENT_CONFIG["password"]
                )
            except Exception:
                logger.error("连接qBittorrent失败，请检查配置项")
                exit()

        if not self.db:
            self.db = Database()

    def check_task_valid(self):
        self._connect(skip_qb=True)  # 先只连接db并检查任务是否合法，避免每次都连接qb导致qb卡顿

        if not self.config_id:
            config_id = self.db.get_config_id(self.info_hash)
            if config_id:
                self.config_id = uuid.UUID(config_id[0])
            else:
                logger.info("未找到指定info_hash「%s」对应的任务，不是发种机提供的任务，跳过", self.info_hash)
                exit()
        else:
            try:
                self.config_id = uuid.UUID(int=int(self.config_id))
            except ValueError:
                self.config_id = uuid.UUID(self.config_id)

        self.torrent_path = os.path.join(
            base_path, "torrents/{}.torrent".format(self.info_hash)
        )
        if not os.path.exists(self.torrent_path):
            logger.error("未找到info_hash「%s」对应的种子文件", self.info_hash)
            exit()

        configs = read_configs()
        config_name = [c for c in configs if configs[c]["id"] == self.config_id]
        if config_name:
            self.config = configs[config_name[0]]
            self.config["config_name"] = config_name[0]
        else:
            logger.error("未找到ID为「%s」的配置项", self.config_id)
            exit()

        self._connect()
        torrents = (
            self.qb.torrents()
        )  # get_torrent(info_hash)并不能获得种子名，因此只能通过获取全部种子来获得种子名
        self.torrent_name = ""
        for torrent in torrents:
            if torrent["hash"] == self.info_hash:
                self.torrent_name = torrent["name"]
                self.torrent = torrent
                break

        if not self.torrent_name:
            logger.error("未在qB中找到info_hash为「%s」的种子", self.info_hash)
            exit()

        logger.info(
            "解析完成，种子「%s」(%s)，使用配置项「%s」",
            self.torrent_name,
            self.info_hash,
            self.config["config_name"],
        )

    def format_torrent_info(self) -> dict:
        info = {"type": "405", "specificcat": "连载", "district": "日漫"}
        params = [
            "cname",  # 中文名
            "ename",  # 英文名
            "issuedate",  # 发行时间
            "animenum",  # 动漫集数
            "substeam",  # 字幕组
            "specificcat",  # 动漫类别
            "format",  # 动漫文件格式
            "resolution",  # 画面分辨率
            "district",  # 动漫国别
            "small_descr",  # 副标题
            "descr",  # 简介
        ]

        if "info" in self.config:
            for param in params:
                if param in self.config["info"]:
                    info[param] = self.config["info"][param]

        for pattern in pattern_group:
            search = re.search(pattern, self.torrent_name)
            if search:
                pattern_result = search.groupdict()
                info["ename"] = (
                    pattern_result["search_name"].replace("_", " ")
                    if pattern_result.get("search_name")
                    else ""
                )
                info["substeam"] = (
                    pattern_result["group"] if pattern_result.get("group") else ""
                )
                info["animenum"] = (
                    pattern_result["episode"].zfill(2)
                    if pattern_result.get("episode")
                    else ""
                )
                info["format"] = (
                    pattern_result["filetype"].upper()
                    if pattern_result.get("filetype")
                    else ""
                )
                break

        info["format"] = self.get_torrent_format(info.get("format", ""))

        resolution = re.findall("(480|720|1080|1440|2160)", self.torrent_name)
        if resolution:
            info["resolution"] = "{}p".format(resolution[0])

        if "cname" not in info or "issuedate" not in info or "descr" not in info:
            bangumi_info = self.get_bangumi_data()
            info = {**bangumi_info, **info}
            info["ename"] = (
                bangumi_info["alternate_name"] if "ename" not in info else info["ename"]
            )

        return info

    def post_to_site(self, torrent_info: dict) -> None:
        try:
            resp = requests.post(
                "https://tjupt.org/takeupload.php",
                data=torrent_info,
                files={"file": open(self.torrent_path, "rb")},
                cookies=parse_cookies(TJUPT_COOKIES_RAW),
            )
        except requests.exceptions.RequestException:
            logger.error("种子「%s」(%s)发布失败，网络错误", self.torrent_name, self.info_hash)
            self.db.set_task_error(self.info_hash)
            return

        if resp.status_code >= 400:
            logger.error(
                "种子「%s」(%s)发布失败，网页返回错误码%s",
                self.torrent_name,
                self.info_hash,
                resp.status_code,
            )
            self.db.set_task_error(self.info_hash)
            return

        tid = re.findall("details\\.php\\?id=(\\d+)&", resp.url)
        if tid:
            tid = tid[0]
            logger.info(
                "种子「%s」(%s)发布成功，种子ID为%s", self.torrent_name, self.info_hash, tid
            )

            self.qb.download_from_link(
                "https://tjupt.org/download.php?id={}".format(tid),
                cookie=TJUPT_COOKIES_RAW,
                savepath=QBITTORRENT_CONFIG["savepath"],
            )
            logger.info("成功推送到qB，开始做种")
            self.db.set_task_done(self.info_hash)
            self.retry_error_tasks()
        elif "该种子已存在" in resp.text:
            tid = re.findall("details\\.php\\?id=(\\d+)&", resp.text)
            if tid:
                tid = tid[0]
                logger.info(
                    "种子「%s」(%s)已存在，种子ID为%s，开始辅种", self.torrent_name, self.info_hash, tid
                )

                self.qb.download_from_link(
                    "https://tjupt.org/download.php?id={}".format(tid),
                    cookie=TJUPT_COOKIES_RAW,
                    savepath=QBITTORRENT_CONFIG["savepath"],
                )
                logger.info("成功推送到qB，开始做种")
                self.db.set_task_done(self.info_hash)
                self.retry_error_tasks()
            else:
                self.db.set_task_error(self.info_hash)
                logger.error(
                    "种子「%s」(%s)已存在，但未解析出种子ID...", self.torrent_name, self.info_hash
                )
        else:
            reason = "未知原因"
            if "上传失败" in resp.text:
                reason = re.findall(
                    '<table width="100%" border="1" cellspacing="0" cellpadding="10"><tr><td class="text">'
                    "(.*?)</td></tr></table></td></tr></table>",
                    resp.text,
                )
                reason = reason[0] if reason else "未知原因"
            elif "login" in resp.url:
                reason = "Cookies过期"

            self.db.set_task_error(self.info_hash)
            logger.error(
                "种子「%s」(%s)发布失败，原因：%s", self.torrent_name, self.info_hash, reason
            )

    def get_bangumi_data(self) -> dict:
        if "bangumi" not in self.config:
            logger.error("无法获取Bangumi ID")
            return {}

        resp = None
        for endpoint in PTGEN_ENDPOINTS:
            try:
                resp = requests.get(endpoint, {"url": self.config["bangumi"]})
                break
            except requests.exceptions.RequestException as exception:
                logger.error("访问PTGEN API时出现网络错误（%s）: %s", endpoint, repr(exception))

        if resp is None:
            logger.error("未能成功从PTGEN APIs中解析数据")
            return {}

        if resp.status_code != 200:
            logger.error("PTGEN API内部错误：%s", resp.url)
            return {}

        data = resp.json()

        if not data["success"]:
            logger.error("PTGEN API报错：%s，地址：%s", data["error"], resp.url)

        logger.debug("获取PTGEN数据成功")
        bangumi_result = {
            "cname": data["name_cn"] if "name_cn" in data else data["name"],
            "alternate_name": data["name"],
        }

        if "air_date" in data:
            split_date = data["air_date"].split("-")
            if len(split_date) >= 2:
                bangumi_result["issuedate"] = "{}年{}月".format(
                    split_date[0], split_date[1]
                )
            elif len(split_date) == 1:
                bangumi_result["issuedate"] = "{}年".format(split_date[0])
            else:
                logger.warning("解析bangumi返回的开播时间「%s」失败", data["air_date"])

        bangumi_result["descr"] = data["format"]

        return bangumi_result

    def get_torrent_format(self, pattern_format):
        with open(self.torrent_path, "rb") as fp:
            torrent = bencoder.decode(fp.read())
        info = torrent[b"info"]
        regex = re.compile("MP4|MKV", re.I)
        name = info[b"name"].decode("utf-8")  # 文件夹名/文件名

        source = "WEBRip" if "web" in name.lower() else "TVRip"

        if pattern_format != "":
            return f"{pattern_format}/{source}"
        else:
            torrent_format = regex.findall(name)
            if torrent_format:
                return f"{torrent_format[0].upper()}/{source}"
            else:
                files = info.get(b"files", [])
                for file in files:
                    torrent_format = regex.findall(
                        "/".join(i.decode("utf-8") for i in file[b"path"])
                    )
                    if torrent_format:
                        return f"{torrent_format[0].upper()}/{source}"
                return source

    def retry_error_tasks(self):
        # 一次只取一个，程序会迭代执行直至所有错误的任务被执行一遍
        info_hash = self.db.get_error_task()
        if info_hash:
            self.run(info_hash[0])


if __name__ == "__main__":
    parse = ArgumentParser()
    parse.add_argument("info_hash", help="种子的info_hash")
    parse.add_argument(
        "-c",
        "--config",
        help="发布时使用的配置项str/int UUID",
        dest="config_id",
        default=None,
    )
    argv = parse.parse_args()

    autoseed = Autoseed()
    if argv.info_hash:
        try:
            autoseed.run(argv.info_hash, argv.config_id)
        except Exception as e:
            traceback.print_exc()
            logger.error("意料之外的错误：%s", repr(e))
    else:
        autoseed.retry_error_tasks()
