import glob
import os
import uuid

from yaml import dump, load

from config import base_path

try:
    from yaml import CDumper as Dumper
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader, Dumper

from utils.logger import logger


def read_configs(path=os.path.join(base_path, "instance/configs/*.yaml")):
    enabled_items = {}

    configs = glob.glob(path)
    for config in configs:
        updated = False
        with open(config, "r") as fp:
            data = load(fp, Loader)
        if data.get("enable", True) and len(data.get("items", [])):
            for item in data.get("items", []):
                this_item = data["items"][item]
                if not this_item.get("id"):
                    this_item["id"] = uuid.uuid4()
                    updated = True
                if this_item.get("enable", True):
                    enabled_items[item] = this_item

        if updated:
            with open(config, "w") as fp:
                dump(data, fp, Dumper, allow_unicode=True)

            cache_path = os.path.join(base_path, "instance/cache.json")
            if os.path.exists(cache_path):
                os.remove(cache_path)
            logger.info("发现新项目，已更新配置文件中对应id数据并清理缓存")

    logger.info("已读取%s个已启用的发布项目", len(enabled_items))
    return enabled_items


if __name__ == "__main__":
    print(read_configs())
