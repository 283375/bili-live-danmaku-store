import argparse
import asyncio
import datetime
import logging
import os
import sys
import json

from bilibili_api import live
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from bili_live_danmaku_store.db import DbBatchWriteQueue, init
from bili_live_danmaku_store.log import LOG_FILE_FORMATTER, LOG_STDOUT_FORMATTER
from bili_live_danmaku_store.models import DANMU_MSG, INTERACT_WORD, Property

logger = logging.getLogger(__name__)
all_events_logger = logging.getLogger("ALL_EVENTS")

parser = argparse.ArgumentParser()
parser.add_argument("room_id", nargs=1, type=int)
args = parser.parse_args()

room_id = args.room_id[0]


db_write_queue = DbBatchWriteQueue()

room = live.LiveDanmaku(room_id, max_retry=12, retry_after=5)


@room.on("DANMU_MSG")
async def on_danmaku(event):
    data = event["data"]

    uid = data["info"][2][0]
    username = data["info"][2][1]
    timestamp = data["info"][0][4]
    content = data["info"][1]
    crc32 = data["info"][0][7]
    have_medal = len(data["info"][3]) > 0
    medal_room_id = data["info"][3][3] if have_medal else None
    medal_level = data["info"][3][0] if have_medal else None
    medal_name = data["info"][3][1] if have_medal else None

    db_write_queue.append_model(
        DANMU_MSG(
            timestamp=timestamp,
            uid=uid,
            username=username,
            medal_room_id=medal_room_id,
            medal_name=medal_name,
            medal_level=medal_level,
            content=content,
            # crc32=crc32,
        )
    )


@room.on("INTERACT_WORD")
async def on_interact_word(event):
    data = event["data"]

    timestamp = data["data"]["timestamp"]
    trigger_time = data["data"]["trigger_time"]
    uid = data["data"]["uid"]
    username = data["data"]["uname"]
    medal_room_id = data["data"]["fans_medal"]["anchor_roomid"] or None
    medal_name = data["data"]["fans_medal"]["medal_name"] or None
    medal_level = data["data"]["fans_medal"]["medal_level"] or None

    db_write_queue.append_model(
        INTERACT_WORD(
            timestamp=timestamp,
            trigger_time=trigger_time,
            uid=uid,
            username=username,
            medal_room_id=medal_room_id,
            medal_name=medal_name,
            medal_level=medal_level,
        )
    )


@room.on("ALL")
async def on_all(event):
    try:
        all_events_logger.debug(json.dumps(event, ensure_ascii=False))
    except Exception:
        all_events_logger.debug(repr(event))


def configure_loggers(log_parent_dir: str):
    logging.getLogger("root").handlers = []

    api_logger = logging.getLogger("bili_live_danmaku_store")
    bilibili_api_logger = logging.getLogger(f"LiveDanmaku_{room_id}")

    log_file = os.path.join(log_parent_dir, "app.log")
    debug_file = os.path.join(log_parent_dir, "debug.log")
    all_events_file = os.path.join(log_parent_dir, "all_events.log")

    info_handler = logging.FileHandler(filename=log_file, encoding="utf-8")
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(LOG_FILE_FORMATTER)
    debug_handler = logging.FileHandler(filename=debug_file, encoding="utf-8")
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(LOG_FILE_FORMATTER)
    all_events_handler = logging.FileHandler(filename=all_events_file, encoding="utf-8")
    all_events_handler.setLevel(logging.DEBUG)
    all_events_handler.setFormatter(logging.Formatter(style="{", fmt="{message}"))
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(LOG_STDOUT_FORMATTER)

    INFO_LOGGERS = [logger, api_logger, bilibili_api_logger]
    DEBUG_LOGGERS = [logger, api_logger, bilibili_api_logger]
    ALL_EVENTS_LOGGERS = [all_events_logger]

    for _logger in INFO_LOGGERS + DEBUG_LOGGERS + ALL_EVENTS_LOGGERS:
        _logger.propagate = False
        _logger.setLevel(logging.DEBUG)
        _logger.handlers = []
    for _logger in INFO_LOGGERS:
        _logger.addHandler(info_handler)
        _logger.addHandler(stdout_handler)
    for _logger in DEBUG_LOGGERS:
        _logger.addHandler(debug_handler)
    for _logger in ALL_EVENTS_LOGGERS:
        _logger.addHandler(all_events_handler)


async def main():
    # init database
    # make sure parent dir exists
    now = datetime.datetime.now()
    datetime_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    parent_dir = os.path.join(os.getcwd(), datetime_str)
    os.makedirs(parent_dir)
    configure_loggers(parent_dir)

    dbfilepath = os.path.abspath(os.path.join(parent_dir, f"room_{room_id}.db"))
    engine = create_engine(f"sqlite:///{dbfilepath}", poolclass=NullPool)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode = WAL;"))
    Session = sessionmaker(engine)

    init(engine)
    db_write_queue.set_sessionmaker(Session)

    with Session() as session:
        session.add(Property(key="app_start", value=datetime_str))
        session.commit()
    db_write_queue.timer.start()
    logger.info(f"Start record {dbfilepath}")
    await room.connect()


def close():
    logger.info("close() called, final commit and exitting program.")
    db_write_queue.close()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        asyncio.run(main())
    except (Exception, KeyboardInterrupt):
        logger.exception("Exception in main loop")
    finally:
        close()
        logger.info("Program exit.")
