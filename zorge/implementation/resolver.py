import types
import typing

from ..definition import contracts


class Resolver:
    def __init__(
        self,
        unit_registry: contracts.ContainerUnitRegistry,
        cache: contracts.InstanceCacheType | None = None,
        context: contracts.ResolverContextType | None = None
    ):
        self._unit_registry = unit_registry
        self._container_cache: contracts.InstanceCacheType = cache if cache is not None else {}
        self._resolver_cache: contracts.InstanceCacheType = {}
        self._resolver_context = context or {}

    async def resolve(
        self,
        contract: contracts.ContractType,
        context: contracts.ResolverContextType | None = None
    ):
        return await self._resolve(
            contract=contract,
            context=context
        )

    async def shutdown(
        self,
        context: contracts.ShutdownContextType | None = None
    ):
        for unit_key, unit in self._unit_registry.items():
            if unit_key.kind == contracts.UnitKeyKind.CALLBACK:
                if unit.cache_scope is contracts.CacheScope.RESOLVER:
                    instance = self._resolver_cache.get(unit.contract)
                    if instance is None:
                        continue
                    if unit.implementation_execution_type is contracts.ImplementationExecutionType.ASYNC:
                        await unit.implementation(instance, context)
                    else:
                        unit.implementation(instance, context)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown(
            context={'exc_type': exc_type, 'exc_val': exc_val, 'exc_tb': exc_tb}
        )

    async def _resolve(
        self,
        contract: contracts.ContractType,
        default: typing.Any | None = None,
        context: contracts.ResolverContextType | None = None
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
                parameter.name: await self._apply_context_parameter(parameter, context)
                for parameter in unit.init_signature.parameters.values()
                if parameter.name not in ('args', 'kwargs')
            } if unit.init_signature else {}
            result = unit.implementation(**params)
        elif unit.implementation_kind is contracts.ImplementationKind.CALLABLE:
            params = {
                parameter.name: await self._apply_context_parameter(parameter, context)
                for parameter in unit.execution_signature.parameters.values()
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

    async def _apply_context_parameter(
        self,
        parameter: contracts.FunctionParameter,
        context: contracts.ResolverContextType
    ):
        args = list(filter(lambda x: x is not types.NoneType, typing.get_args(parameter.type)))
        if len(args) > 1:
            raise Exception("Cannot resolve more than 1 contract")
        elif len(args) == 1:
            _type = args[0]
        else:
            _type = parameter.type

        if _type in context:
            return context.get(_type)
        elif parameter.name in context:
            return context.get(parameter.name)
        else:
            return await self._resolve(_type, parameter.default)
