import collections.abc
import functools
import inspect
import typing
import itertools

from .. import contracts, exceptions
from . import resolver


class Container:
    def __init__(self):
        self._unit_registry: contracts.internal.ContainerUnitRegistry = {}
        self._callback_registry: collections.abc.MutableSequence[contracts.internal.ContainerUnit] = []
        self._cache: contracts.internal.InstanceCacheType = {}

    def register_dependency(
        self,
        implementation: contracts.internal.ImplementationType,
        contract: contracts.internal.ContractType | None = None,
        cache_scope: typing.Literal['container', 'resolver'] | None = None,
    ):
        if cache_scope == 'container':
            cache_scope = contracts.CacheScope.CONTAINER
        elif cache_scope == 'resolver':
            cache_scope = contracts.CacheScope.RESOLVER
        contract = self._derive_implementation_contract(implementation, contract)
        implementation_kind = self._derive_implementation_kind(implementation)
        implementation_execution_type = self._derive_implementation_execution_type(implementation)
        init_signature = None
        execution_signature = None
        if implementation_kind is contracts.internal.ImplementationKind.CLASS:
            init_signature = self._derive_parameters(getattr(implementation, '__init__'))
        elif implementation_kind is contracts.internal.ImplementationKind.CALLABLE:
            execution_signature = self._derive_parameters(
                implementation if inspect.isfunction(implementation) else getattr(implementation, '__call__')
            )

        self._unit_registry[contract] = contracts.internal.ContainerUnit(
            contract=contract,
            implementation=implementation,
            implementation_kind=implementation_kind,
            implementation_execution_type=implementation_execution_type,
            cache_scope=cache_scope,
            init_signature=init_signature,
            execution_signature=execution_signature
        )

    def register_callback(
        self,
        contract: contracts.internal.ContractType,
        callback: contracts.CallbackType,
        trigger: typing.Literal['shutdown'],
    ):
        if trigger == 'shutdown':
            trigger = contracts.ImplementationExecutionTrigger.SHUTDOWN

        execution_signature = self._derive_parameters(
            callback if inspect.isfunction(callback) else getattr(callback, '__call__')
        )
        self._callback_registry.append(
            contracts.internal.ContainerUnit(
                contract=contract,
                implementation=callback,
                implementation_kind=contracts.internal.ImplementationKind.CALLBACK,
                implementation_execution_type=self._derive_implementation_execution_type(callback),
                implementation_execution_trigger=trigger,
                cache_scope=self._unit_registry.get(contract).cache_scope,
                execution_signature=execution_signature
            )
        )

    def get_resolver(self) -> resolver.Resolver:
        return resolver.Resolver(
            unit_registry=self._unit_registry,
            callback_registry=self._callback_registry,
            global_cache=self._cache
        )

    async def shutdown(self, exc_type: typing.Any | None = None):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown(exc_type)

    def __iter__(self) -> collections.abc.Generator[contracts.internal.ContainerUnit, None, None]:
        for unit in itertools.chain(self._unit_registry.values(), self._callback_registry):
            yield unit

    def __add__(self, other: typing.Self) -> typing.Self:
        for unit in other:
            if unit.implementation_kind == contracts.internal.ImplementationKind.CALLBACK:
                self._callback_registry.append(unit)
            else:
                self._unit_registry[unit.contract] = unit
        return self

    @staticmethod
    def _derive_implementation_contract(
        implementation: contracts.ImplementationType,
        contract: contracts.ContractType | None = None
    ):
        if contract is None:
            if inspect.isfunction(implementation):
                signature = inspect.signature(implementation)
                return signature.return_annotation
            elif inspect.isclass(implementation):
                try:
                    return implementation.__mro__[1]
                except IndexError:
                    raise exceptions.CannotAutomaticallyDeriveContract(implementation)
            else:
                raise exceptions.CannotAutomaticallyDeriveContract(implementation)
        return contract

    @staticmethod
    def _derive_parameters(
        func: typing.Callable
    ):
        if not inspect.isfunction(func):
            return None
        signature = inspect.signature(func)
        return contracts.internal.FunctionSignature(
            parameters={
                param_name: contracts.internal.FunctionParameter(
                    type=param_type.annotation,
                    default=None if param_type.default is inspect.Parameter.empty else param_type.default
                )
                for param_name, param_type
                in signature.parameters.items()
                if param_name != 'self'
            },
            result=signature.return_annotation
        )

    @staticmethod
    def _derive_implementation_kind(
        implementation: contracts.ImplementationType
    ) -> contracts.internal.ImplementationKind:
        if inspect.isclass(implementation):
            return contracts.internal.ImplementationKind.CLASS
        elif inspect.iscoroutinefunction(implementation):
            return contracts.internal.ImplementationKind.CALLABLE
        elif inspect.isfunction(implementation):
            return contracts.internal.ImplementationKind.CALLABLE
        elif isinstance(implementation, functools.partial):
            return contracts.internal.ImplementationKind.CALLABLE
        else:
            return contracts.internal.ImplementationKind.STATIC

    @staticmethod
    def _derive_implementation_execution_type(
        implementation: contracts.ImplementationType
    ):
        if inspect.iscoroutinefunction(implementation):
            return contracts.internal.ImplementationExecutionType.ASYNC
        elif inspect.isfunction(implementation):
            return contracts.internal.ImplementationExecutionType.SYNC
        elif hasattr(implementation, '__call__'):
            if inspect.iscoroutinefunction(implementation.__call__):
                return contracts.internal.ImplementationExecutionType.ASYNC
            else:
                return contracts.internal.ImplementationExecutionType.SYNC
