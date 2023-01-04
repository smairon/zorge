import typing
import collections.abc

from .. import contracts
from .generic import success_shutdown_instance, failure_shutdown_instance
from .provider import DependencyProvider


def _auto_detect_contract(
    instance: contracts.DependencyBindingInstance,
    contract: contracts.DependencyBindingContract | None
) -> contracts.DependencyBindingContract | None:
    if contract:
        return contract
    parent = None
    for cls in instance.__mro__:
        if cls == typing.Protocol:
            return parent
        parent = cls


class BindingChain(contracts.DependencyBindingChain):
    def __init__(self, dependency_registry: contracts.DependencyBingingRegistry):
        self._dependency_registry = dependency_registry

    def filter(self, clause: contracts.DependencyBindingChainFilterClause) -> 'BindingChain':
        self._dependency_registry = {
            contract: record
            for contract, record in self._dependency_registry.items()
            if clause(contract, record)
        }
        return self

    def map(
        self,
        key_clause: contracts.DependencyBindingChainMapClause,
        value_clause: contracts.DependencyBindingChainMapClause
    ) -> 'BindingChain':
        self._dependency_registry = {
            key_clause(contract, record): value_clause(contract, record)
            for contract, record in self._dependency_registry.items()
        }
        return self

    def items(self) -> contracts.DependencyBingingRegistry:
        return self._dependency_registry

    def values(self) -> collections.abc.Iterable[contracts.DependencyBindingRecord]:
        return self._dependency_registry.values()

    def keys(self) -> collections.abc.Iterable[contracts.DependencyBindingContract]:
        return self._dependency_registry.keys()


class DependencyContainer(contracts.DependencyContainer):
    def __init__(self):
        self._dependency_registry = {}
        self._callbacks = {}
        self._instance_registry = {}

    def register_dependency(
        self,
        instance: contracts.DependencyBindingInstance,
        contract: contracts.DependencyBindingContract,
        binding_type: contracts.DependencyBindingType,
        scope: contracts.DependencyBindingScope = contracts.DependencyBindingScope.GLOBAL
    ) -> typing.NoReturn:
        contract = _auto_detect_contract(instance, contract)
        if contract:
            self._dependency_registry[contract] = contracts.DependencyBindingRecord(binding_type, instance, scope)

    def register_contractual_dependency(
        self,
        instance: contracts.DependencyBindingInstance,
        contract: contracts.DependencyBindingContract | None = None
    ) -> typing.NoReturn:
        contract = _auto_detect_contract(instance, contract)
        self.register_dependency(
            instance,
            contract,
            contracts.DependencyBindingType.CONTRACTUAL
        )

    def register_selfish_dependency(
        self,
        instance: contracts.DependencyBindingInstance,
        singleton_scope: contracts.DependencyBindingScope | None = None
    ) -> typing.NoReturn:
        binding_type = contracts.DependencyBindingType.SELFISH
        scope = contracts.DependencyBindingScope.GLOBAL

        if singleton_scope:
            binding_type = contracts.DependencyBindingType.SINGLETON
            scope = singleton_scope

        self.register_dependency(
            instance,
            instance,
            binding_type,
            scope
        )

    def register_global_singleton(
        self,
        instance: contracts.DependencyBindingInstance,
        contract: contracts.DependencyBindingContract | None = None,
    ) -> typing.NoReturn:
        self.register_dependency(
            instance,
            contract,
            contracts.DependencyBindingType.SINGLETON
        )

    def register_instance_singleton(
        self,
        instance: contracts.DependencyBindingInstance,
        contract: contracts.DependencyBindingContract | None = None,
    ) -> typing.NoReturn:
        self.register_dependency(
            instance,
            contract,
            contracts.DependencyBindingType.SINGLETON,
            contracts.DependencyBindingScope.INSTANCE
        )

    def register_callback(
        self,
        callback: typing.Callable,
        contract: contracts.DependencyBindingContract,
        event_type: contracts.EventType
    ) -> typing.NoReturn:
        self._callbacks[contract] = contracts.CallbackRecord(event_type, callback)

    def register_shutdown_callback(
        self,
        success_callback: typing.Callable,
        failure_callback: typing.Callable,
        contract: contracts.DependencyBindingContract
    ):
        self._callbacks[(contract, contracts.EventType.ON_SHUTDOWN_SUCCESS)] = success_callback
        self._callbacks[(contract, contracts.EventType.ON_SHUTDOWN_FAILURE)] = failure_callback

    def get_bindings(self) -> BindingChain:
        return BindingChain(self._dependency_registry)

    def get_provider(self) -> DependencyProvider:
        return DependencyProvider(
            bindings=self._dependency_registry,
            callbacks=self._callbacks,
            instance_registry=self._instance_registry,
        )

    async def shutdown(self, exc_type: typing.Any) -> typing.NoReturn:
        for key, callback in self._callbacks.items():
            _contract, _type = key
            _desired = contracts.EventType.ON_SHUTDOWN_FAILURE if exc_type else contracts.EventType.ON_SHUTDOWN_SUCCESS
            if _type == _desired:
                singleton_instance = self._get_from_registry(_contract)
                if exc_type:
                    await failure_shutdown_instance(callback, singleton_instance, exc_type)
                else:
                    await success_shutdown_instance(callback, singleton_instance)

    def _get_from_registry(
        self,
        contract: contracts.DependencyBindingContract
    ) -> contracts.DependencyBindingInstance:
        return self._instance_registry.get(contract)
