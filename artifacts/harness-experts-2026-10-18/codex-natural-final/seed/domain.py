from dataclasses import dataclass


@dataclass(frozen=True)
class TaskRow:
    task_id: int
    title: str
    complete: int

    @classmethod
    def from_tuple(cls, row):
        return cls(row[0], row[1], row[2])


@dataclass(frozen=True)
class Task:
    task_id: int
    title: str
    done: bool
    marker: str

    @classmethod
    def from_row(cls, row):
        done = bool(row.complete)
        return cls(row.task_id, row.title, done, "x" if done else " ")

    def to_mapping(self):
        return {"id": self.task_id, "title": self.title, "done": self.done}

    def to_markdown(self):
        return f"- [{self.marker}] {self.title}"


class TaskProjection:
    def mappings(self, tasks):
        return [self.project(task) for task in tasks]

    def project(self, task):
        mapped = task.to_mapping()
        return {"id": mapped["id"], "title": mapped["title"], "done": mapped["done"]}

    def markdown(self, tasks):
        return [task.to_markdown() for task in tasks]
