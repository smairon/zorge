import collections.abc
import types
import typing

from ..definition import contracts

ContextType: typing.TypeAlias = collections.abc.Mapping[contracts.ContractType, collections.abc.Mapping]


class Resolver:
    def __init__(
        self,
        unit_registry: contracts.ContainerUnitRegistry,
        cache: contracts.InstanceCacheType | None = None,
        context: ContextType | None = None
    ):
        self._unit_registry = unit_registry
        self._container_cache: contracts.InstanceCacheType = cache if cache is not None else {}
        self._resolver_cache: contracts.InstanceCacheType = {}
        self._resolver_context = context or {}

    async def resolve(
        self,
        contract: contracts.ContractType,
        context: ContextType | None = None
    ):
        return await self._resolve(
            contract=contract,
            context=context
        )

    async def shutdown(self, exc_type, exc_val):
        for unit_key, unit in self._unit_registry.items():
            if unit_key.kind == contracts.UnitKeyKind.CALLBACK:
                if unit.cache_scope is contracts.CacheScope.RESOLVER:
                    instance = self._resolver_cache.get(unit.contract)
                    if unit.implementation_execution_type is contracts.ImplementationExecutionType.ASYNC:
                        await unit.implementation(instance, {'exc_type': exc_type, 'exc_val': exc_val})
                    else:
                        unit.implementation(instance, {'exc_type': exc_type, 'exc_val': exc_val})

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown(exc_type, exc_val)

    async def _resolve(
        self,
        contract: contracts.ContractType,
        default: typing.Any | None = None,
        context: ContextType | None = None
    ):

        if contract in self._resolver_context:
            return self._resolver_context.get(contract)
        if contract in self._resolver_cache:
            return self._resolver_cache.get(contract)
        if contract in self._container_cache:
            return self._container_cache.get(contract)
        if (
            unit := self._unit_registry.get(
                contracts.UnitKey(
                    contract=contract,
                    kind=contracts.UnitKeyKind.DEPENDENCY)
            )
        ) is None:
            return default

        context = context or {}
        result = None
        if unit.implementation_kind is contracts.ImplementationKind.STATIC:
            result = unit.implementation
        elif unit.implementation_kind is contracts.ImplementationKind.CLASS:
            params = {
                k: context.get(k) or await self._apply_context_value(v)
                for k, v in unit.init_signature.parameters.items()
                if k not in ('args', 'kwargs')
            } if unit.init_signature else {}
            result = unit.implementation(**params)
        elif unit.implementation_kind is contracts.ImplementationKind.CALLABLE:
            params = {
                k: context.get(k) or await self._apply_context_value(v)
                for k, v in unit.execution_signature.parameters.items()
            } if unit.execution_signature else {}
            if unit.implementation_execution_type is contracts.ImplementationExecutionType.ASYNC:
                result = await unit.implementation(**params)
            else:
                result = unit.implementation(**params)

        if result is not None:
            if unit.cache_scope is contracts.CacheScope.RESOLVER:
                self._resolver_cache[contract] = result
            elif unit.cache_scope is contracts.CacheScope.CONTAINER:
                self._container_cache[contract] = result

        return result

    async def _apply_context_value(
        self,
        value: contracts.FunctionParameter,
    ):
        args = list(filter(lambda x: x is not types.NoneType, typing.get_args(value.type)))
        if len(args) > 1:
            raise Exception("Cannot resolve more than 1 contract")
        elif len(args) == 1:
            _type = args[0]
        else:
            _type = value.type

        return await self._resolve(_type, value.default)
