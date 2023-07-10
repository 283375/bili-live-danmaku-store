from typing import Optional

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class TableBase(DeclarativeBase):
    pass


class Property(TableBase):
    __tablename__ = "properties"

    key: Mapped[str] = mapped_column(String(), primary_key=True)
    value: Mapped[str] = mapped_column(String())


class DANMU_MSG(TableBase):
    __tablename__ = "DANMU_MSG"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)

    timestamp: Mapped[int] = mapped_column(Integer())
    uid: Mapped[int] = mapped_column(Integer())
    username: Mapped[str] = mapped_column(String())
    medal_room_id: Mapped[Optional[int]] = mapped_column(Integer(), nullable=True)
    medal_name: Mapped[Optional[str]] = mapped_column(String(), nullable=True)
    medal_level: Mapped[Optional[int]] = mapped_column(Integer(), nullable=True)
    content: Mapped[str] = mapped_column(String())
    # crc32: Mapped[str] = mapped_column(String())


class INTERACT_WORD(TableBase):
    __tablename__ = "INTERACT_WORD"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)

    timestamp: Mapped[int] = mapped_column(Integer())
    trigger_time: Mapped[int] = mapped_column(Integer())
    uid: Mapped[int] = mapped_column(Integer())
    username: Mapped[str] = mapped_column(String())
    medal_room_id: Mapped[Optional[int]] = mapped_column(Integer(), nullable=True)
    medal_name: Mapped[Optional[str]] = mapped_column(String(), nullable=True)
    medal_level: Mapped[Optional[int]] = mapped_column(Integer(), nullable=True)
