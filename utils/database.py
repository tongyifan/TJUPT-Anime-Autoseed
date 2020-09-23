import os
import sqlite3

from config import base_path
from utils.logger import logger


class Database:
    def __init__(self, database=os.path.join(base_path, "instance/autoseed.sqlite3")):
        self.database = database
        self.cursor = None
        if os.path.exists(database):
            self.connect_to_database()
        else:
            logger.warning("未找到数据库文件，新建文件并建表")
            open(database, "a").close()
            self.connect_to_database()
            self.create_tables()

    def connect_to_database(self):
        conn = sqlite3.connect(self.database, isolation_level=None)
        self.cursor = conn.cursor()
        logger.debug("连接数据库成功")

    def create_tables(self):
        logger.debug("开始新建数据表")
        self.cursor.execute(
            """CREATE TABLE tasks
                            (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                            config_id TEXT NOT NULL,
                            info_hash TEXT NOT NULL UNIQUE,
                            done INTEGER NOT NULL DEFAULT 0);"""
        )

        logger.info("新建数据表成功")

    def insert_task(self, config_id, info_hash):
        try:
            self.cursor.execute(
                "INSERT INTO tasks (config_id, info_hash) VALUES (?, ?)",
                (
                    config_id,
                    info_hash,
                ),
            )
        except sqlite3.IntegrityError:
            logger.warning("重复任务：%s", info_hash)
            return 0

        logger.info("插入数据库成功：%s", info_hash)
        return self.cursor.rowcount

    def get_config_id(self, info_hash):
        self.cursor.execute(
            "SELECT config_id FROM tasks WHERE info_hash = ? ORDER BY id DESC LIMIT 1",
            (info_hash,),
        )
        return self.cursor.fetchone()

    def set_task_done(self, info_hash):
        self.cursor.execute(
            "UPDATE tasks SET done = 1 WHERE info_hash = ?", (info_hash,)
        )
