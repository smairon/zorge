import typing
import enum
import collections.abc

ContractType = typing.Any
ImplementationType = typing.Any

CallbackContextType = collections.abc.Mapping[str, typing.Any]
CallbackType = collections.abc.Callable[[ContractType, CallbackContextType], typing.NoReturn]


class ImplementationExecutionTrigger(enum.Enum):
    SHUTDOWN = enum.auto()


class CacheScope(enum.Enum):
    CONTAINER = enum.auto()
    RESOLVER = enum.auto()


class ShutdownCallbackContext(typing.TypedDict):
    exc_type: type[Exception]
    exc_val: Exception
