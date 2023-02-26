import typing


class ServiceContract(typing.Protocol):
    def get_connection_pool(self) -> int: ...

    def is_feature_enabled(self) -> bool: ...

    def __getitem__(self, item): ...


class StorageContract(typing.Protocol):
    def is_connection_established(self) -> bool: ...

    def is_connection_closed(self) -> bool: ...

    def get_connection_pool(self) -> int: ...

    def __getitem__(self, item): ...
