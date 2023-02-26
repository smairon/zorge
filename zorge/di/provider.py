import inspect
import typing
import collections.abc
import itertools

from .. import contracts, exceptions
from .generic import shutdown, startup


class DependencyProvider(contracts.DependencyProvider):
    def __init__(
        self,
        bindings: contracts.DependencyBingingRegistry,
        callbacks: typing.Iterable[contracts.DependencyBindingRecord],
        literals: typing.Mapping,
        container_singleton_registry: contracts.SingletonRegistry
    ):
        self._bindings = bindings
        self._callbacks = callbacks
        self._literals = literals
        self._container_singleton_registry = container_singleton_registry
        self._provider_singleton_registry: contracts.SingletonRegistry = {}

    async def get(
        self,
        contract: contracts.DependencyBindingContract,
        context: contracts.ContextType | None = None
    ):
        result = await self._resolve(contract, context=context)
        if result is contracts.NotDefined:
            result = None
        return result

    def __getitem__(self, contract: contracts.DependencyBindingContract):
        return self._get_singleton(contract)

    async def __aenter__(self):
        await self.startup()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.shutdown(exc_type)

    def __iter__(self) -> typing.Generator[contracts.DependencyBindingRecord, None, None]:
        for record in itertools.chain(self._bindings.values(), self._callbacks):
            yield record

    async def shutdown(self, exc_type: typing.Any):
        await shutdown(self, exc_type, contracts.DependencyBindingScope.INSTANCE)

    async def startup(self):
        await startup(self)

    def get_registry(
        self
    ) -> collections.abc.Mapping[
        contracts.DependencyBindingContract,
        contracts.DependencyBindingRecord
    ]:
        return self._provider_singleton_registry

    async def _resolve(
        self,
        contract: contracts.DependencyBindingContract,
        context: contracts.ContextType | None
    ):
        binding_record = self._bindings.get(contract)
        if not binding_record:
            return contracts.NotDefined

        if (
            binding_record.binding_type == contracts.DependencyBindingType.SINGLETON and
            isinstance(context, collections.abc.Mapping) and
            contract in context
        ):
            raise exceptions.CannotPassContextToSingleton(contract=contract)

        if result := self._get_singleton(contract):
            return result

        instance = binding_record.instance

        if inspect.iscoroutinefunction(instance):
            result = await instance()
        elif not inspect.isclass(instance):
            result = instance
        else:
            init_spec = inspect.getfullargspec(getattr(instance, '__init__'))
            params = {}
            for param_name, param_type in init_spec.annotations.items():
                value = contracts.NotDefined
                if isinstance(context, collections.abc.Mapping) and contract in context:
                    value = context[contract].get(param_name, contracts.NotDefined)
                if value is contracts.NotDefined and self._literals:
                    value = self._literals.get(param_name, contracts.NotDefined)
                if value is contracts.NotDefined:
                    value = await self._resolve(param_type, context=context)
                if value is not contracts.NotDefined:
                    params[param_name] = value
            try:
                result = instance(**params)
            except TypeError as e:
                raise exceptions.CannotResolveParams(contract=contract, message=str(e))

        self._register_singleton(contract, result)

        return result

    def _get_singleton(
        self,
        contract: contracts.DependencyBindingContract
    ):
        instance = self._provider_singleton_registry.get(contract)
        if not instance:
            instance = self._container_singleton_registry.get(contract)
        return instance

    def _register_singleton(
        self,
        contract: contracts.DependencyBindingContract,
        instance: contracts.SingletonInstance
    ):
        binding_record = self._bindings.get(contract)
        if not binding_record:
            return
        if binding_record.binding_type != contracts.DependencyBindingType.SINGLETON:
            return

        if binding_record.scope == contracts.DependencyBindingScope.INSTANCE:
            self._provider_singleton_registry[contract] = instance
        else:
            self._container_singleton_registry[contract] = instance
