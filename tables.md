# 数据库格式

## kx-alpha-0.0.2

```sql
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

CREATE TABLE INTERACT_WORD (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    INTEGER,
    uid          INTEGER,
    username     TEXT,
    medal_name   TEXT,
    medal_level  INTEGER
)

CREATE TABLE properties (
    key    TEXT UNIQUE NOT NULL,
    value  TEXT
)
```
