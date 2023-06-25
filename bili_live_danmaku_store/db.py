from datetime import datetime
import logging
import sqlite3
from threading import Lock, Timer

from .models import BaseInsert, DanmakuInsert, InteractWordInsert


def get_conn(filename_stem):
    conn = sqlite3.connect(f"{filename_stem}.db")
    conn.execute("PRAGMA journal_mode = WAL;")

    return conn


def init_db(filename_stem):
    conn = get_conn(filename_stem)

    with conn:
        cursor = conn.cursor()
        init_sqls = [
            """
            CREATE TABLE DANMU_MSG (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp    INTEGER,
                uid          INTEGER,
                username     TEXT,
                medal_name   TEXT,
                medal_level  INTEGER,
                content      TEXT,
                crc32        TEXT
            )
            """,
            """
            CREATE TABLE INTERACT_WORD (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp    INTEGER,
                uid          INTEGER,
                username     TEXT,
                medal_name   TEXT,
                medal_level  INTEGER
            )
            """,
            """
            CREATE TABLE properties (
                key    TEXT UNIQUE NOT NULL,
                value  TEXT
            )
            """,
            "INSERT INTO properties VALUES ('version', 'kx-alpha-0.0.2')",
        ]
        [cursor.execute(init_sql) for init_sql in init_sqls]


class RepeatTimer(Timer):
    """
    https://stackoverflow.com/a/48741004/16484891
    CC BY-SA 3.0
    """

    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class DbBatchWriteQueue:
    def __init__(self, filename_stem: str):
        self.__lock = Lock()

        self.__filename_stem = filename_stem

        self.__DANMU_MSG: list[DanmakuInsert] = []
        self.__INTERACT_WORD: list[InteractWordInsert] = []
        self.__inserts: list[list[BaseInsert]] = [
            self.__DANMU_MSG,
            self.__INTERACT_WORD,
        ]

        self.append_DANMU_MSG = self.append_wrapper(self.__DANMU_MSG)
        self.append_INTERACT_WORD = self.append_wrapper(self.__INTERACT_WORD)

        self.timer = RepeatTimer(10.0, self.commit)

    def append_wrapper(self, __list: list, /):
        def wrapper(datacls, /):
            self.__lock.acquire()
            __list.append(datacls)
            self.__lock.release()

        return wrapper

    def commit(self):
        self.__lock.acquire()
        try:
            with get_conn(self.__filename_stem) as conn:
                cursor = conn.cursor()
                insert_num = 0
                for insert_list in self.__inserts:
                    if not insert_list:
                        continue
                    insert_clause = insert_list[0].insert_clause()
                    cursor.executemany(
                        insert_clause, [datacls.param_list() for datacls in insert_list]
                    )
                    insert_num += len(insert_list)
                cursor.close()
                conn.commit()
            logging.info(f"Wrote {insert_num} entries into database.")
        except Exception:
            logging.exception("db write fail")
            logging.warning("following queue cleared")
            [logging.warning(repr(l)) for l in self.__inserts]
        finally:
            [l.clear() for l in self.__inserts]
            self.__lock.release()

    def close(self):
        self.timer.cancel()
        self.commit()
        with get_conn(self.__filename_stem) as conn:
            cursor = conn.cursor()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            cursor.execute(f"INSERT INTO properties VALUES ('end_record', '{now_str}')")
            cursor.close()
