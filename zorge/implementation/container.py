import collections.abc
import functools
import inspect
import typing

from ..definition import contracts, exceptions
from . import resolver


class Container:
    def __init__(self):
        self._unit_registry: contracts.ContainerUnitRegistry = {}
        self._cache: contracts.InstanceCacheType = {}

    def register_dependency(
        self,
        implementation: contracts.ImplementationType,
        contract: contracts.ContractType | None = None,
        cache_scope: typing.Literal['container', 'resolver'] | None = None,
    ):
        if cache_scope == 'container':
            cache_scope = contracts.CacheScope.CONTAINER
        elif cache_scope == 'resolver':
            cache_scope = contracts.CacheScope.RESOLVER
        else:
            cache_scope = None
        contract = self._derive_implementation_contract(implementation, contract)
        implementation_kind = self._derive_implementation_kind(implementation)
        implementation_execution_type = self._derive_implementation_execution_type(implementation)
        init_signature = None
        execution_signature = None
        if implementation_kind is contracts.ImplementationKind.CLASS:
            init_signature = self._derive_parameters(getattr(implementation, '__init__'))
        elif implementation_kind is contracts.ImplementationKind.CALLABLE:
            execution_signature = self._derive_parameters(
                implementation if inspect.isfunction(implementation) else getattr(implementation, '__call__')
            )

        self._unit_registry[
            contracts.UnitKey(contract=contract, kind=contracts.UnitKeyKind.DEPENDENCY)
        ] = contracts.ContainerUnit(
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
        contract: contracts.ContractType,
        callback: contracts.CallbackType,
        trigger: typing.Literal['shutdown'] = 'shutdown',
    ):
        if trigger == 'shutdown':
            trigger = contracts.ImplementationExecutionTrigger.SHUTDOWN
        else:
            raise exceptions.UnsupportedTrigger(contract, trigger)

        execution_signature = self._derive_parameters(
            callback if inspect.isfunction(callback) else getattr(callback, '__call__')
        )

        unit_key = contracts.UnitKey(
            contract=contract,
            kind=contracts.UnitKeyKind.CALLBACK
        )
        self._unit_registry[unit_key] = (
            contracts.ContainerUnit(
                contract=contract,
                implementation=callback,
                implementation_kind=contracts.ImplementationKind.CALLBACK,
                implementation_execution_type=self._derive_implementation_execution_type(callback),
                implementation_execution_trigger=trigger,
                cache_scope=self._unit_registry.get(
                    contracts.UnitKey(
                        contract=contract,
                        kind=contracts.UnitKeyKind.DEPENDENCY
                    )
                ).cache_scope,
                execution_signature=execution_signature
            )
        )

    def get_resolver(self) -> resolver.Resolver:
        return resolver.Resolver(
            unit_registry=self._unit_registry,
            cache=self._cache
        )

    async def shutdown(self, exc_type: typing.Any | None = None):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown(exc_type)

    def __iter__(self) -> collections.abc.Iterator[contracts.ContainerUnit]:
        for unit in self._unit_registry.values():
            yield unit

    def __add__(self, other: typing.Self) -> typing.Self:
        for unit in other:
            if unit.implementation_kind == contracts.ImplementationKind.CALLBACK:
                unit_key_kind = contracts.UnitKeyKind.CALLBACK
            else:
                unit_key_kind = contracts.UnitKeyKind.DEPENDENCY
            self._unit_registry[
                contracts.UnitKey(contract=unit.contract, kind=unit_key_kind)
            ] = unit
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
        return contracts.FunctionSignature(
            parameters={
                param_name: contracts.FunctionParameter(
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
    ) -> contracts.ImplementationKind:
        if inspect.isclass(implementation):
            return contracts.ImplementationKind.CLASS
        elif inspect.iscoroutinefunction(implementation):
            return contracts.ImplementationKind.CALLABLE
        elif inspect.isfunction(implementation):
            return contracts.ImplementationKind.CALLABLE
        elif isinstance(implementation, functools.partial):
            return contracts.ImplementationKind.CALLABLE
        else:
            return contracts.ImplementationKind.STATIC

    @staticmethod
    def _derive_implementation_execution_type(
        implementation: contracts.ImplementationType
    ):
        if inspect.iscoroutinefunction(implementation):
            return contracts.ImplementationExecutionType.ASYNC
        elif inspect.isfunction(implementation):
            return contracts.ImplementationExecutionType.SYNC
        elif hasattr(implementation, '__call__'):
            if inspect.iscoroutinefunction(implementation.__call__):
                return contracts.ImplementationExecutionType.ASYNC
            else:
                return contracts.ImplementationExecutionType.SYNC
