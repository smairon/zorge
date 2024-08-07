import typing

DBEngineContract = typing.NewType('DBEngineContract', object)


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
