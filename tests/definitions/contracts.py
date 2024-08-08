import dataclasses
import typing

DBEngineContract = typing.NewType('DBEngineContract', object)
PoolSizeContract = typing.NewType('PoolSizeContract', int)

class UserActorContract(typing.Protocol):
    def get_id(self) -> int: ...


class PostActorContract(typing.Protocol):
    def get_id(self) -> int: ...


class UserServiceContract(typing.Protocol):
    def get_ids(self) -> list[int]: ...


class DBConnectionContract(typing.Protocol):
    def register_connection_closed(self, sentinel: int): ...


class RepositoryContract(typing.Protocol):
    def do(self) -> str: ...


class UsersRepositoryContract(RepositoryContract):
    pass


class PostsRepositoryContract(RepositoryContract):
    pass


class UnitOfWorkContract:
    def do(self) -> tuple[str, str]: ...


@dataclasses.dataclass
class UserContextContract:
    user_id: int
