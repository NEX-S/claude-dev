from contextlib import closing
from dataclasses import dataclass
import sqlite3

from domain import TaskRow


@dataclass(frozen=True)
class DatabaseLocation:
    path: str

    def database_path(self):
        return self.path


class ConnectionFactory:
    def __init__(self, location):
        self.location = location

    def open(self):
        return sqlite3.connect(self.location.database_path())


class ReadRetryPolicy:
    def run(self, read):
        for attempt in range(2):
            try:
                return read()
            except sqlite3.OperationalError:
                if attempt == 1:
                    raise


class SQLiteBackend:
    def __init__(self, connections, retry):
        self.connections = connections
        self.retry = retry

    def _transaction(self, operation):
        with closing(self.connections.open()) as database:
            # Commit before a result reaches stdout.
            with database:
                database.execute(
                    "CREATE TABLE IF NOT EXISTS tasks ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, "
                    "done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1)))"
                )
                return operation(database)

    def insert(self, title):
        def write(database):
            cursor = database.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
            return cursor.lastrowid
        return self._transaction(write)

    def complete(self, task_id):
        def write(database):
            cursor = database.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
            if cursor.rowcount == 0:
                raise ValueError(f"task ID {task_id} does not exist")
        return self._transaction(write)

    def read(self):
        def select(database):
            return [TaskRow.from_tuple(row) for row in database.execute(
                "SELECT id, title, done FROM tasks ORDER BY id"
            )]
        return self.retry.run(lambda: self._transaction(select))


class BackendRegistry:
    def __init__(self, location):
        self.location = location
        self.factories = {"sqlite": self._sqlite}

    def _sqlite(self):
        return SQLiteBackend(ConnectionFactory(self.location), ReadRetryPolicy())

    def get(self, engine):
        return self.factories[engine]()
