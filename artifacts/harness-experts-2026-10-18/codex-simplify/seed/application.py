from dataclasses import dataclass

from domain import TaskProjection
from persistence import BackendRegistry, DatabaseLocation
from repository import TaskRepository


@dataclass(frozen=True)
class Settings:
    database: str
    engine: str = "sqlite"


class TaskService:
    def __init__(self, repository, projection):
        self.repository = repository
        self.projection = projection

    def add(self, title):
        if not title.strip():
            raise ValueError("title must not be blank")
        return self.repository.add(title)

    def done(self, task_id):
        self.repository.mark_done(task_id)

    def records(self):
        return self.projection.mappings(self.repository.all())

    def markdown(self):
        return self.projection.markdown(self.repository.all())


class TaskGateway:
    def __init__(self, service):
        self.service = service

    def add(self, title):
        return self.service.add(title)

    def done(self, task_id):
        self.service.done(task_id)

    def records(self):
        return self.service.records()

    def markdown(self):
        return self.service.markdown()


def build_gateway(database_path):
    settings = Settings(database_path)
    location = DatabaseLocation(settings.database)
    backend = BackendRegistry(location).get(settings.engine)
    repository = TaskRepository(backend)
    service = TaskService(repository, TaskProjection())
    return TaskGateway(service)
