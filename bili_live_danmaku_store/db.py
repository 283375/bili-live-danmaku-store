import logging
from datetime import datetime
from threading import Lock, Timer
from typing import Type

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from .models import Property, TableBase

logger = logging.getLogger(__name__)


def init(engine: Engine, checkfirst=False):
    TableBase.metadata.create_all(engine, checkfirst=checkfirst)


class RepeatTimer(Timer):
    """
    https://stackoverflow.com/a/48741004/16484891
    CC BY-SA 3.0
    """

    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class DbBatchWriteQueue:
    def __init__(self):
        self.__lock = Lock()

        self.__sessionmaker: Type[Session] | None = None

        self.__models = []
        self.append_model = self.append_wrapper(self.__models)

        self.timer = RepeatTimer(10.0, self.commit)

    def set_sessionmaker(self, __sessionmaker):
        """
        ```py
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(...)
        queue = DbBatchWriteQueue()
        queue.set_sessionmaker(Session)
        ```
        """
        self.__sessionmaker = __sessionmaker

    def append_wrapper(self, __list: list, /):
        def wrapper(__value, /):
            self.__lock.acquire()
            __list.append(__value)
            self.__lock.release()

        return wrapper

    def commit(self):
        self.__lock.acquire()

        if self.__sessionmaker is None or not callable(self.__sessionmaker):
            logger.critical("sessionmaker not set!")

        try:
            with self.__sessionmaker() as session:
                session.add_all(self.__models)
                session.commit()
            logger.info(f"Wrote {len(self.__models)} entries into database.")
        except Exception:
            logger.exception("Error occured while inserting to database:")
            logger.error(
                "Rolling back transaction and discarding the following items:"
                + "\n".join(m.__dict__ for m in self.__models)
            )
        finally:
            self.__models.clear()
            self.__lock.release()

    def close(self):
        self.timer.cancel()
        self.commit()

        if callable(self.__sessionmaker):
            session = self.__sessionmaker()
            if isinstance(session, Session):
                with session:
                    session.add(
                        Property(
                            key="end_record",
                            value=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                        )
                    )
