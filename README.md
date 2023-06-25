# bili-live-danmaku-store

记录 B 站直播间弹幕/入场信息。

> **Warning**
>
> 早期开发阶段，任何方法、类甚至模块名称、布局等都可能发生改变。
>
> Use it at your own risk.

## 依赖

[Nemo2011/bilibili-api](https://github.com/Nemo2011/bilibili-api)

```sh
$ pip install bilibili-api-python
```

## 使用

```sh
$ python index.py 22182132
```

会在当前工作目录创建以时间戳命名 (%Y-%m-%d_%H-%M-%S) 的文件夹，内含数据库及日志文件。

### 目录结构

```
.
│  index.py
│  
├─2023-06-25_17-54-15
│      room_22182132.db
│      room_22182132.debug.log
│      room_22182132.log
│      
├─bili_live_danmaku_store
│  │  db.py
│  │  log.py
│  │  models.py
│  │  __init__.py
│  │  
│  └─__pycache__
└─__pycache__

```

### 日志示例

```log
[root 2023-06-25 17:54:15 INFO]@21060: Start record N:\git_repositories\283375\bili-live-danmaku-store\2023-06-25_17-54-15\room_22182132
[LiveDanmaku_22182132 2023-06-25 17:54:15 INFO]@21060: 准备连接直播间 22182132
[LiveDanmaku_22182132 2023-06-25 17:54:15 INFO]@21060: 准备连接直播间 22182132
[httpx 2023-06-25 17:54:15 INFO]@21060: HTTP Request: GET https://api.live.bilibili.com/xlive/web-room/v1/index/getRoomPlayInfo?room_id=22182132 "HTTP/1.1 200 OK"
[httpx 2023-06-25 17:54:15 INFO]@21060: HTTP Request: GET https://api.live.bilibili.com/xlive/web-room/v1/index/getRoomPlayInfo?room_id=22182132 "HTTP/1.1 200 OK"
[httpx 2023-06-25 17:54:16 INFO]@21060: HTTP Request: GET https://api.live.bilibili.com/room/v1/Danmu/getConf?room_id=22182132 "HTTP/1.1 200 OK"
[httpx 2023-06-25 17:54:16 INFO]@21060: HTTP Request: GET https://api.live.bilibili.com/room/v1/Danmu/getConf?room_id=22182132 "HTTP/1.1 200 OK"
[LiveDanmaku_22182132 2023-06-25 17:54:16 INFO]@21060: 正在尝试连接主机： wss://broadcastlv.chat.bilibili.com:443/sub
[LiveDanmaku_22182132 2023-06-25 17:54:16 INFO]@21060: 正在尝试连接主机： wss://broadcastlv.chat.bilibili.com:443/sub
[LiveDanmaku_22182132 2023-06-25 17:54:16 INFO]@21060: 连接服务器并认证成功
[LiveDanmaku_22182132 2023-06-25 17:54:16 INFO]@21060: 连接服务器并认证成功
[root 06-25 17:54:26 INFO]@21924: Wrote 32 entries into database.
[root 06-25 17:54:36 INFO]@21924: Wrote 54 entries into database.
[root 06-25 17:54:46 INFO]@21924: Wrote 29 entries into database.
[httpx 06-25 17:54:47 INFO]@21060: HTTP Request: GET https://live-trace.bilibili.com/xlive/rdata-interface/v1/heartbeat/webHeartBeat?pf=web&hb=NjB8OTI2MTN8MXww "HTTP/1.1 200 OK"
[httpx 06-25 17:54:47 INFO]@21060: HTTP Request: GET https://live-trace.bilibili.com/xlive/rdata-interface/v1/heartbeat/webHeartBeat?pf=web&hb=NjB8OTI2MTN8MXww "HTTP/1.1 200 OK"
[root 06-25 17:54:57 INFO]@21924: Wrote 31 entries into database.
```

### --help

```sh
$ python index.py --help
usage: index.py [-h] room_id

positional arguments:
  room_id

options:
  -h, --help  show this help message and exit
```

## 数据库格式

见 [tables.md](./tables.md)。
