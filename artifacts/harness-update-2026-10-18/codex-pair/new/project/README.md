# 本地任务账本

只依赖 Python 3 标准库，无需安装依赖。数据库路径由 `--db` 指定；文件不存在时自动创建，所在目录需要已存在。

```sh
python3 tasks.py --db ./tasks.db add "学习 Python 标准库"
python3 tasks.py --db ./tasks.db add "buy milk"
python3 tasks.py --db ./tasks.db list
python3 tasks.py --db ./tasks.db done 1
python3 tasks.py --db ./tasks.db export
```

- `add TITLE`：保留标题原文，拒绝空字符串或全为空白的标题，输出新任务的整数 ID。
- `list`：按 ID 递增输出 JSON 数组，每项只有 `id`、`title`、`done`；空账本输出 `[]`。
- `done ID`：标记已有任务完成，成功时没有输出；重复完成同一任务也成功。不存在的 ID 报错。
- `export`：按 ID 递增输出 Markdown 清单，空账本没有输出。

含空格的标题应使用 shell 引号。参数错误、数据库错误和无效操作均以非零状态退出，原因写到 stderr。

数据保存在 SQLite 中。使用参数化 SQL 和事务，在写入提交成功后才输出新 ID，避免提交失败却输出成功结果。没有额外服务、配置或第三方依赖。

运行真实命令行入口的行为检查：

```sh
python3 -m unittest -v
```
