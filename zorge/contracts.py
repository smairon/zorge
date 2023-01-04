import collections.abc
import enum
import typing
from collections import namedtuple

DependencyBindingContract = typing.Type
DependencyBindingInstance = typing.Any
DependencyBindingRecord = namedtuple('DependencyBindingRecord', ['type', 'instance', 'scope'])
DependencyBingingRegistry = collections.abc.MutableMapping[DependencyBindingContract, DependencyBindingRecord]

CallbackRegistry = collections.abc.MutableMapping[DependencyBindingContract, typing.Callable]

SingletonInstance = typing.Any
SingletonInstanceRegistry = collections.abc.MutableMapping[DependencyBindingContract, SingletonInstance]

ContextType = collections.abc.Mapping[
    tuple[DependencyBindingContract, str], typing.Any
]

DependencyBindingChainFilterClause = typing.Callable[
    [DependencyBindingContract, DependencyBindingRecord],
    bool
]

DependencyBindingChainMapClause = typing.Callable[
    [DependencyBindingContract, DependencyBindingRecord],
    typing.Any
]


class DependencyBindingType(enum.Enum):
    CONTRACTUAL = enum.auto()
    SELFISH = enum.auto()
    SINGLETON = enum.auto()


class DependencyBindingScope(enum.Enum):
    GLOBAL = enum.auto()
    INSTANCE = enum.auto()


class EventType(enum.Enum):
    ON_START = enum.auto()
    ON_SHUTDOWN_SUCCESS = enum.auto()
    ON_SHUTDOWN_FAILURE = enum.auto()


class DependencyBindingChain(typing.Protocol):
    def filter(
        self,
        clause: DependencyBindingChainFilterClause
    ) -> 'DependencyBindingChain': ...

    def map(
        self,
        key_clause: DependencyBindingChainMapClause,
        value_clause: DependencyBindingChainMapClause
    ) -> 'DependencyBindingChain': ...

    def items(self) -> collections.abc.Mapping: ...

    def keys(self) -> collections.abc.Iterable: ...

    def values(self) -> collections.abc.Iterable: ...


class DependencyProvider(typing.Protocol):
    async def resolve(
        self,
        contract: DependencyBindingContract,
        context: ContextType | None = None
    ): ...

    async def shutdown(self, exc_type: typing.Any): ...

    async def __aenter__(self): ...

    async def __aexit__(self, exc_type, exc, tb): ...


class DependencyContainer(typing.Protocol):
    def register_contractual_dependency(
        self,
        instance: DependencyBindingInstance,
        contract: DependencyBindingContract | None = None
    ) -> typing.NoReturn: ...

    def register_selfish_dependency(
        self,
        instance: DependencyBindingInstance
    ) -> typing.NoReturn: ...

    def register_global_singleton(
        self,
        instance: DependencyBindingInstance,
        contract: DependencyBindingContract | None = None,
    ) -> typing.NoReturn: ...

    def register_instance_singleton(
        self,
        instance: DependencyBindingInstance,
        contract: DependencyBindingContract | None = None,
    ) -> typing.NoReturn: ...

    def register_dependency(
        self,
        instance: DependencyBindingInstance,
        contract: DependencyBindingContract,
        binding_type: DependencyBindingType,
        scope: DependencyBindingScope = DependencyBindingScope.GLOBAL
    ) -> typing.NoReturn: ...

    def register_callback(
        self,
        callback: typing.Callable,
        contract: DependencyBindingContract,
        event_type: EventType
    ): ...

    def register_shutdown_callback(
        self,
        success_callback: typing.Callable,
        failure_callback: typing.Callable,
        contract: DependencyBindingContract,
    ): ...

    def get_bindings(self) -> DependencyBindingChain: ...

    def get_provider(self) -> DependencyProvider: ...

    async def shutdown(self, exc_type: typing.Any): ...
