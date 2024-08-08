import dataclasses
import typing
import enum
import collections.abc

ContractType: typing.TypeAlias = type
ImplementationType: typing.TypeAlias = typing.Any
ResolverContextType: typing.TypeAlias = collections.abc.Mapping[str | ContractType, typing.Any]
CallbackContextType: typing.TypeAlias = collections.abc.Mapping[str, typing.Any]
ShutdownContextType: typing.TypeAlias = collections.abc.Mapping[str, typing.Any]
CallbackType: typing.TypeAlias = collections.abc.Callable[[ImplementationType, CallbackContextType], typing.NoReturn]
InstanceType: typing.TypeAlias = typing.Any


class ImplementationExecutionTrigger(enum.Enum):
    SHUTDOWN = enum.auto()


class CacheScope(enum.Enum):
    CONTAINER = enum.auto()
    RESOLVER = enum.auto()


class UnitKeyKind(enum.Enum):
    DEPENDENCY = enum.auto()
    CALLBACK = enum.auto()


class ImplementationKind(enum.Enum):
    CALLABLE = enum.auto()
    CLASS = enum.auto()
    STATIC = enum.auto()
    CALLBACK = enum.auto()


class ImplementationExecutionType(enum.Enum):
    SYNC = enum.auto()
    ASYNC = enum.auto()


@dataclasses.dataclass(frozen=True)
class UnitKey:
    kind: UnitKeyKind
    contract: ContractType | None


@dataclasses.dataclass
class FunctionParameter:
    name: str
    type: type
    default: typing.Any | None


@dataclasses.dataclass
class FunctionSignature:
    parameters: collections.abc.Mapping[str, FunctionParameter]
    result: type


@dataclasses.dataclass
class ContainerUnit:
    contract: ContractType
    implementation: ImplementationType
    implementation_kind: ImplementationKind
    implementation_execution_type: ImplementationExecutionType | None = None
    implementation_execution_trigger: ImplementationExecutionTrigger | None = None
    cache_scope: CacheScope | None = None
    init_signature: FunctionSignature | None = None
    execution_signature: FunctionSignature | None = None


ContainerUnitRegistry: typing.TypeAlias = collections.abc.MutableMapping[UnitKey, ContainerUnit]
InstanceCacheType: typing.TypeAlias = collections.abc.MutableMapping[ContractType, InstanceType]
