import abc
import asyncio
import collections.abc

from .contracts import (
    DBEngineContract,
    DBConnectionContract,
    UsersRepositoryContract,
    PostsRepositoryContract
)


def sync_engine():
    return 'postgresql'


async def async_engine() -> str:
    await asyncio.sleep(0.1)
    return 'postgresql'


async def close_connection(connection: DBConnectionContract, context: collections.abc.Mapping):
    connection.register_connection_closed(1)


class DBConnection:
    def __init__(self, db_engine: DBEngineContract):
        self._db_engine = db_engine
        self.sentinel = None

    def register_connection_closed(self, sentinel: int):
        self.sentinel = sentinel

    def __str__(self):
        return f'Connection with {self._db_engine}'


class Repository(abc.ABC):
    def __init__(self, db_connection: DBConnectionContract):
        self._db_connection = db_connection

    def do(self):
        return f'{self.__class__.__name__} using {self._db_connection}'


class UsersRepository(Repository):
    pass


class PostsRepository(Repository):
    pass


class UnitOfWork:
    def __init__(
        self,
        users_repo: UsersRepositoryContract,
        posts_repo: PostsRepositoryContract
    ):
        self._users_repo = users_repo
        self._posts_repo = posts_repo

    def do(self) -> tuple[str, str]:
        return self._users_repo.do(), self._posts_repo.do()
