import collections.abc
import typing
import dataclasses
import enum

from .domain import (
    ImplementationExecutionTrigger,
    CacheScope,
    ContractType,
    ImplementationType
)

InstanceType = typing.Any


class ImplementationKind(enum.Enum):
    CALLABLE = enum.auto()
    CLASS = enum.auto()
    STATIC = enum.auto()
    CALLBACK = enum.auto()


class ImplementationExecutionType(enum.Enum):
    SYNC = enum.auto()
    ASYNC = enum.auto()


@dataclasses.dataclass
class FunctionParameter:
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


ContainerUnitRegistry = collections.abc.MutableMapping[ContractType, ContainerUnit]
InstanceCacheType = collections.abc.MutableMapping[ContractType, InstanceType]
