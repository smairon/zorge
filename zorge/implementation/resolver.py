import collections.abc
import types
import typing

from .. import contracts


class Resolver:
    def __init__(
        self,
        unit_registry: contracts.internal.ContainerUnitRegistry,
        callback_registry: collections.abc.MutableSequence[contracts.internal.ContainerUnit],
        global_cache: contracts.internal.InstanceCacheType | None = None
    ):
        self._unit_registry = unit_registry
        self._callback_registry = callback_registry
        self._global_cache = global_cache or {}
        self._local_cache: contracts.internal.InstanceCacheType = {}
        self._context = None

    def add_context(
        self,
        contract: contracts.ContractType,
        data: collections.abc.Mapping
    ):
        self._context = self._context or {contract: data}

    async def resolve(
        self,
        contract: contracts.ContractType,
        execution_context: collections.abc.Mapping[str, typing.Any] | None = None,
        initial_context: collections.abc.Mapping[str, typing.Any] | None = None
    ):
        return await self._resolve(
            contract=contract,
            execution_context=execution_context,
            initial_context=initial_context
        )

    async def shutdown(self, exc_type, exc_val):
        for callback_unit in self._callback_registry:
            if callback_unit.cache_scope is contracts.CacheScope.RESOLVER:
                instance = self._local_cache.get(callback_unit.contract)
                if callback_unit.implementation_execution_type is contracts.internal.ImplementationExecutionType.ASYNC:
                    await callback_unit.implementation(instance, {'exc_type': exc_type, 'exc_val': exc_val})
                else:
                    callback_unit.implementation(instance, {'exc_type': exc_type, 'exc_val': exc_val})

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown(exc_type, exc_val)

    async def _resolve(
        self,
        contract: contracts.ContractType,
        default: typing.Any | None = None,
        execution_context: collections.abc.Mapping[str, typing.Any] | None = None,
        initial_context: collections.abc.Mapping[str, typing.Any] | None = None
    ):
        if self._context and contract in self._context:
            return self._context.get(contract)
        if contract in self._local_cache:
            return self._local_cache.get(contract)
        if contract in self._global_cache:
            return self._global_cache.get(contract)
        if (unit := self._unit_registry.get(contract)) is None:
            return default

        result = None
        if unit.implementation_kind is contracts.internal.ImplementationKind.STATIC:
            result = unit.implementation
        elif unit.implementation_kind is contracts.internal.ImplementationKind.CLASS:
            params = {
                k: await self._apply_context_value(k, v, initial_context)
                for k, v in unit.init_signature.parameters.items()
                if k not in ('args', 'kwargs')
            } if unit.init_signature else {}
            result = unit.implementation(**params)
        elif unit.implementation_kind is contracts.internal.ImplementationKind.CALLABLE:
            params = {
                k: await self._apply_context_value(k, v, execution_context)
                for k, v in unit.execution_signature.parameters.items()
            } if unit.execution_signature else {}
            if unit.implementation_execution_type is contracts.internal.ImplementationExecutionType.ASYNC:
                result = await unit.implementation(**params)
            else:
                result = unit.implementation(**params)

        if result is not None:
            if unit.cache_scope is contracts.CacheScope.RESOLVER:
                self._local_cache[contract] = result
            elif unit.cache_scope is contracts.CacheScope.CONTAINER:
                self._global_cache[contract] = result

        return result

    async def _apply_context_value(
        self,
        key: str,
        value: contracts.internal.FunctionParameter,
        context: collections.abc.Mapping[str, typing.Any]
    ):
        if context and key in context:
            return context.get(key)

        args = list(filter(lambda x: x is not types.NoneType, typing.get_args(value.type)))
        if len(args) > 1:
            raise Exception("Cannot resolve more than 1 contract")
        elif len(args) == 1:
            _type = args[0]
        else:
            _type = value.type

        return await self._resolve(_type, value.default)
