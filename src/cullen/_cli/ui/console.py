from abc import ABC, abstractmethod
from contextlib import AbstractContextManager

INDENT = "  "


class Task(ABC):
    @abstractmethod
    def describe(self, description: str) -> None:
        pass

    @abstractmethod
    def advance(self) -> None:
        pass


class Stage(ABC):
    @abstractmethod
    def tree(self, lines: list[str]) -> None:
        pass

    @abstractmethod
    def line(self, text: str, style: str | None = None) -> None:
        pass


class Console(ABC):
    @abstractmethod
    def line(self, text: str, style: str | None = None) -> None:
        pass

    @abstractmethod
    def stage(self, header: str) -> AbstractContextManager[Stage]:
        pass

    @abstractmethod
    def summary(self, rows: list[tuple[str, str]]) -> None:
        pass

    @abstractmethod
    def progress(self, description: str, total: int | None = None) -> AbstractContextManager[Task]:
        pass
