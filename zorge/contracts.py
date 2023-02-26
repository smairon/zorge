import collections.abc
import enum
import typing
import dataclasses

NotDefined = ...

DependencyBindingContract = typing.Type
DependencyBindingInstance = typing.Any

CallbackRegistry = collections.abc.MutableMapping[DependencyBindingContract, typing.Callable]

SingletonInstance = typing.Any
SingletonRegistry = collections.abc.MutableMapping[DependencyBindingContract, SingletonInstance]

ContextType = collections.abc.Mapping[
    DependencyBindingContract,
    collections.abc.Mapping[str, typing.Any]
]


class DependencyBindingType(enum.Enum):
    CONTRACTUAL = enum.auto()
    SINGLETON = enum.auto()
    LITERAL = enum.auto()
    ON_STARTUP_CALLBACK = enum.auto()
    ON_SHUTDOWN_SUCCESS_CALLBACK = enum.auto()
    ON_SHUTDOWN_FAILURE_CALLBACK = enum.auto()


class DependencyBindingScope(enum.Enum):
    APPLICATION = enum.auto()
    INSTANCE = enum.auto()


@dataclasses.dataclass
class DependencyBindingRecord:
    instance: DependencyBindingInstance
    binding_type: DependencyBindingType = dataclasses.field(default=DependencyBindingType.CONTRACTUAL)
    contract: DependencyBindingContract | None = dataclasses.field(default=None)
    scope: DependencyBindingScope = dataclasses.field(default=DependencyBindingScope.APPLICATION)


class DependencyProvider(typing.Protocol):
    async def get(
        self,
        contract: DependencyBindingContract,
        context: ContextType | None = None
    ): ...

    def get_registry(self) -> collections.abc.Mapping[DependencyBindingContract, DependencyBindingRecord]: ...

    async def shutdown(self, exc_type: typing.Any): ...

    async def __aenter__(self): ...

    async def __aexit__(self, exc_type, exc, tb): ...

    def __iter__(self) -> typing.Generator[DependencyBindingRecord, None, None]: ...


class DependencyContainer(typing.Protocol):
    def register(
        self,
        instance: DependencyBindingInstance,
        contract: DependencyBindingContract | None = None,
        binding_type: DependencyBindingType | None = DependencyBindingType.CONTRACTUAL,
        scope: DependencyBindingScope | None = DependencyBindingScope.APPLICATION
    ) -> typing.NoReturn: ...

    def get_provider(self) -> DependencyProvider: ...

    def get_registry(self) -> collections.abc.Mapping[DependencyBindingContract, DependencyBindingRecord]: ...

    async def shutdown(self, exc_type: typing.Any) -> typing.NoReturn: ...

    def __iter__(self) -> typing.Generator[DependencyBindingRecord, None, None]: ...


DependencyBingingRegistry = collections.abc.MutableMapping[
    DependencyBindingContract,
    DependencyBindingRecord
]
