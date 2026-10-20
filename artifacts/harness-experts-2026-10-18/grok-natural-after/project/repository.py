from domain import Task


class TaskRepository:
    def __init__(self, backend):
        self.backend = backend

    def add(self, title):
        return self.backend.insert(title)

    def mark_done(self, task_id):
        self.backend.complete(task_id)

    def all(self):
        return [Task.from_row(row) for row in self.backend.read()]
