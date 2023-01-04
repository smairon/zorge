import inspect
import typing

from .. import contracts
from .generic import success_shutdown_instance, failure_shutdown_instance


class DependencyProvider(contracts.DependencyProvider):
    def __init__(
        self,
        bindings: contracts.DependencyBingingRegistry,
        callbacks: contracts.CallbackRegistry,
        instance_registry: contracts.SingletonInstanceRegistry
    ):
        self._dependency_registry = bindings
        self._callbacks = callbacks
        self._global_instance_registry = instance_registry
        self._local_instance_registry: contracts.SingletonInstanceRegistry = {}

    async def resolve(
        self,
        contract: contracts.DependencyBindingContract,
        context: contracts.ContextType | None = None
    ):
        context = context or {}
        result = await self._resolve(contract, context=context)
        return result

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.shutdown(exc_type)

    async def shutdown(self, exc_type: typing.Any):
        for key, callback in self._callbacks.items():
            _contract, _type = key
            _desired = contracts.EventType.ON_SHUTDOWN_FAILURE if exc_type else contracts.EventType.ON_SHUTDOWN_SUCCESS
            if _type == _desired:
                singleton_instance = self._get_from_registry(
                    _contract,
                    filter_by_scope=contracts.DependencyBindingScope.INSTANCE
                )
                if exc_type:
                    await failure_shutdown_instance(callback, singleton_instance, exc_type)
                else:
                    await success_shutdown_instance(callback, singleton_instance)

    async def _resolve(
        self,
        contract: contracts.DependencyBindingContract,
        context: contracts.ContextType
    ):
        binding_record = self._dependency_registry.get(contract)
        if not binding_record:
            return

        if result := self._get_from_registry(contract):
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
                if value := context.get((contract, param_name)):
                    params[param_name] = value
                else:
                    params[param_name] = await self._resolve(param_type, context=context)
            result = instance(**params)

        self._add_to_registry(contract, result)

        return result

    def _get_from_registry(
        self,
        contract: contracts.DependencyBindingContract,
        filter_by_scope: contracts.DependencyBindingScope = contracts.DependencyBindingScope.GLOBAL
    ):
        registries = [self._local_instance_registry]
        if filter_by_scope == contracts.DependencyBindingScope.INSTANCE:
            registries.append(self._global_instance_registry)

        for registry in registries:
            if contract in registry:
                return registry.get(contract)

    def _add_to_registry(self, contract: contracts.DependencyBindingContract, instance: contracts.SingletonInstance):
        binding_record = self._dependency_registry.get(contract)
        if not binding_record:
            return
        if binding_record.type != contracts.DependencyBindingType.SINGLETON:
            return

        if binding_record.scope == contracts.DependencyBindingScope.INSTANCE:
            self._local_instance_registry[contract] = instance
        else:
            self._global_instance_registry[contract] = instance
