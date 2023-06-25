from contextlib import suppress
from dataclasses import dataclass


@dataclass
class BaseInsert:
    def preserve_fields(self):
        return ["_table_name"]

    def fields(self):
        fields = list(self.__dataclass_fields__.keys())
        with suppress(ValueError):
            [fields.remove(pf) for pf in self.preserve_fields()]
        return fields

    def insert_clause(self, table_name: str = None) -> str:
        if table_name is None and hasattr(self, "_table_name"):
            table_name = self._table_name

        assert table_name, "Unexpected empty table name"

        fields = self.fields()
        return (
            f"INSERT INTO {table_name} ("
            + ", ".join(fields)
            + ") VALUES ("
            + ", ".join("?" * len(fields))
            + ")"
        )

    def param_list(self) -> list:
        fields = self.fields()
        return [self.__getattribute__(field) for field in fields]


@dataclass(kw_only=True)
class DanmakuInsert(BaseInsert):
    _table_name: str = "DANMU_MSG"
    timestamp: int
    uid: int
    username: str
    medal_name: str
    medal_level: int
    content: str
    crc32: str


@dataclass(kw_only=True)
class InteractWordInsert(BaseInsert):
    _table_name: str = "INTERACT_WORD"
    timestamp: int
    uid: int
    username: str
    medal_name: str
    medal_level: int
