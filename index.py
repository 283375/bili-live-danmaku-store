import argparse
import asyncio
import datetime
import logging
import os

from bilibili_api import live

from bili_live_danmaku_store.db import DbBatchWriteQueue, init_db
from bili_live_danmaku_store.log import configure_logger
from bili_live_danmaku_store.models import DanmakuInsert, InteractWordInsert

parser = argparse.ArgumentParser()
parser.add_argument("room_id", nargs=1, type=int)
args = parser.parse_args()

room_id = args.room_id[0]
now = datetime.datetime.now()
datetime_str = now.strftime("%Y-%m-%d_%H-%M-%S")
parent_dir = os.path.join(os.getcwd(), datetime_str)
os.makedirs(parent_dir)
filename_stem = os.path.join(parent_dir, f"room_{room_id}")

db_write_queue = DbBatchWriteQueue(filename_stem)

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
    medal_level = data["info"][3][0] if have_medal else None
    medal_name = data["info"][3][1] if have_medal else None

    db_write_queue.append_DANMU_MSG(
        DanmakuInsert(
            timestamp=timestamp,
            uid=uid,
            username=username,
            medal_name=medal_name,
            medal_level=medal_level,
            content=content,
            crc32=crc32,
        )
    )


@room.on("INTERACT_WORD")
async def on_interact_word(event):
    data = event["data"]

    timestamp = data["data"]["timestamp"]
    uid = data["data"]["uid"]
    username = data["data"]["uname"]
    medal_name = data["data"]["fans_medal"]["medal_name"] or None
    medal_level = data["data"]["fans_medal"]["medal_level"] or None

    db_write_queue.append_INTERACT_WORD(
        InteractWordInsert(
            timestamp=timestamp,
            uid=uid,
            username=username,
            medal_name=medal_name,
            medal_level=medal_level,
        )
    )


async def main():
    init_db(filename_stem)

    # get root loggers
    logger_names = [
        "root",
        *[name.split(".")[0] for name in logging.root.manager.loggerDict],
    ]
    [configure_logger(logging.getLogger(name), filename_stem) for name in logger_names]

    db_write_queue.timer.start()
    logging.info(f"Start record {filename_stem}")
    await room.connect()


def close():
    logging.info("close() called, final commit and exitting program.")
    db_write_queue.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except Exception as e:
        logging.exception(str(e))
    finally:
        close()
        logging.info("Program exit.")
