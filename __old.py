import argparse
import atexit
import datetime
import logging
import sqlite3
import sys
from threading import Lock, Timer

from livedanmaku import danmaku

parser = argparse.ArgumentParser()
parser.add_argument("room_id", nargs=1, type=int)
args = parser.parse_args()

room_id = args.room_id[0]
datetime_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename_stem = f"{datetime_str}_r{room_id}"


def configure_logger(logger: logging.Logger):
    logger.handlers = []

    logger.setLevel(logging.DEBUG)

    log_file_formatter = logging.Formatter(
        style="{",
        fmt="[{name} {asctime} {levelname}]@{thread}: {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    log_stdout_formatter = logging.Formatter(
        style="{",
        fmt="[{name} {asctime} {levelname}]@{thread}: {message}",
        datefmt="%m-%d %H:%M:%S",
    )

    log_file_handler = logging.FileHandler(
        filename=f"{filename_stem}.log", encoding="utf-8"
    )
    log_file_handler.setLevel(logging.INFO)
    log_file_handler.setFormatter(log_file_formatter)

    log_debug_file_handler = logging.FileHandler(
        filename=f"{filename_stem}.debug.log", encoding="utf-8"
    )
    log_debug_file_handler.setLevel(logging.DEBUG)
    log_debug_file_handler.setFormatter(log_file_formatter)

    log_stdout_handler = logging.StreamHandler(sys.stdout)
    log_stdout_handler.setLevel(logging.INFO)
    log_stdout_handler.setFormatter(log_stdout_formatter)

    logger.addHandler(log_file_handler)
    logger.addHandler(log_debug_file_handler)
    logger.addHandler(log_stdout_handler)


def get_conn():
    conn = sqlite3.connect(f"{filename_stem}.db")
    conn.execute("PRAGMA journal_mode = WAL;")

    return conn


def init_db():
    conn = get_conn()

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
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


lock = Lock()


class DbBatchWriteQueue:
    def __init__(self):
        self.DANMU_MSG = []
        self.INTERACT_WORD = []
        self.timer = RepeatTimer(10.0, self.commit)

    def append_DANMU_MSG(
        self, *, timestamp, uid, username, medal_name, medal_level, content, crc32
    ):
        lock.acquire()
        self.DANMU_MSG.append(
            (timestamp, uid, username, medal_name, medal_level, content, crc32)
        )
        lock.release()

    def append_INTERACT_WORD(
        self, *, timestamp, uid, username, medal_name, medal_level
    ):
        lock.acquire()
        self.INTERACT_WORD.append((timestamp, uid, username, medal_name, medal_level))
        lock.release()

    def commit(self):
        lock.acquire()
        try:
            with get_conn() as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    """
                    INSERT INTO DANMU_MSG
                        (timestamp, uid, username, medal_name, medal_level, content, crc32)
                    VALUES
                        (?, ?, ?, ?, ?, ?, ?)
                    """,
                    self.DANMU_MSG,
                )
                cursor.executemany(
                    """
                    INSERT INTO INTERACT_WORD
                        (timestamp, uid, username, medal_name, medal_level)
                    VALUES
                        (?, ?, ?, ?, ?)
                    """,
                    self.INTERACT_WORD,
                )
                cursor.close()
                conn.commit()
            logging.info(
                f"Wrote {len(self.DANMU_MSG) + len(self.INTERACT_WORD)} entries into database."
            )
        except Exception:
            logging.exception("db write fail")
            logging.warning("following queue cleared")
            logging.warning(repr(self.DANMU_MSG))
            logging.warning(repr(self.INTERACT_WORD))
        finally:
            self.DANMU_MSG.clear()
            self.INTERACT_WORD.clear()
            lock.release()

    def close(self):
        self.timer.cancel()
        self.commit()


client = danmaku.Danmaku()
db_write_queue = DbBatchWriteQueue()
# client.set_cookie_file("cookie.txt")


@client.processor("DANMU_MSG")
def process_danmu_msg(data):
    uid = data["info"][2][0]
    username = data["info"][2][1]
    timestamp = data["info"][0][4]
    content = data["info"][1]
    crc32 = data["info"][0][7]
    medal_level = data["info"][3][0]
    medal_name = data["info"][3][1]
    db_write_queue.append_DANMU_MSG(
        timestamp=timestamp,
        uid=uid,
        username=username,
        medal_name=medal_name,
        medal_level=medal_level,
        content=content,
        crc32=crc32,
    )


@client.processor("INTERACT_WORD")
def process_interact_word(data):
    timestamp = data["data"]["timestamp"]
    uid = data["data"]["uid"]
    username = data["data"]["uname"]
    medal_name = data["data"]["fans_medal"]["medal_name"]
    medal_level = data["data"]["fans_medal"]["medal_level"]

    db_write_queue.append_INTERACT_WORD(
        timestamp=timestamp,
        uid=uid,
        username=username,
        medal_name=medal_name,
        medal_level=medal_level,
    )


@client.processor("NO_IMPL")
def process_no_impl(event):
    # write not implemeted type of data to log files.
    pass


try:
    init_db()

    client.connect(room_id)

    db_write_queue.timer.start()
    atexit.register(db_write_queue.close)

    [
        configure_logger(logging.getLogger(name))
        for name in logging.root.manager.loggerDict
    ]
    configure_logger(logging.getLogger("root"))

    logging.info(f"Start record {filename_stem}")

    client.wait()
except KeyboardInterrupt:
    print("Bye!")
    exit(0)
