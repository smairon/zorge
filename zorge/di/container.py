import typing
import itertools
import collections.abc

from .. import contracts, exceptions
from .generic import shutdown
from .provider import DependencyProvider


class DependencyContainer(contracts.DependencyContainer):
    def __init__(
        self,
        bindings: collections.abc.Iterable[contracts.DependencyBindingRecord] | None = None
    ):
        self._bindings = {}
        self._callbacks = []
        self._literals = {}
        if bindings:
            for record in bindings:
                self.register(
                    instance=record.instance,
                    contract=record.contract,
                    binding_type=record.binding_type,
                    scope=record.scope
                )
        self._container_singleton_registry = {}

    def register(
        self,
        instance: contracts.DependencyBindingInstance,
        contract: contracts.DependencyBindingContract | None = None,
        binding_type: contracts.DependencyBindingType | None = contracts.DependencyBindingType.CONTRACTUAL,
        scope: contracts.DependencyBindingScope | None = contracts.DependencyBindingScope.APPLICATION
    ) -> typing.NoReturn:
        if binding_type == contracts.DependencyBindingType.LITERAL:
            if not isinstance(instance, typing.Mapping):
                raise exceptions.LiteralMustBeMapping(instance=instance)
            else:
                self._literals |= instance

        elif binding_type in (
            contracts.DependencyBindingType.ON_STARTUP_CALLBACK,
            contracts.DependencyBindingType.ON_SHUTDOWN_FAILURE_CALLBACK,
            contracts.DependencyBindingType.ON_SHUTDOWN_SUCCESS_CALLBACK
        ):
            if not callable(instance):
                raise exceptions.CallbackInstanceMustBeCallable(instance=instance, contract=contract)

            self._callbacks.append(
                contracts.DependencyBindingRecord(
                    binding_type=binding_type,
                    instance=instance,
                    contract=contract,
                    scope=scope
                )
            )
        else:
            contract = self._detect_contract(instance, contract)
            if not contract:
                raise exceptions.ContractNotDefined(instance=instance, contract=contract)

            self._bindings[contract] = contracts.DependencyBindingRecord(
                binding_type=binding_type,
                instance=instance,
                contract=contract,
                scope=scope
            )
        self._integrity_check()

    def get_provider(self) -> DependencyProvider:
        return DependencyProvider(
            bindings=self._bindings,
            callbacks=self._callbacks,
            literals=self._literals,
            container_singleton_registry=self._container_singleton_registry
        )

    def get_registry(
        self
    ) -> collections.abc.Mapping[contracts.DependencyBindingContract, contracts.DependencyBindingRecord]:
        return self._container_singleton_registry

    async def shutdown(self, exc_type: typing.Any) -> typing.NoReturn:
        await shutdown(self, exc_type, contracts.DependencyBindingScope.APPLICATION)

    @staticmethod
    def _detect_contract(
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

    def _integrity_check(self):
        for callback_record in self._callbacks:
            binding_record = self._bindings.get(callback_record.contract)
            if binding_record and binding_record.binding_type != contracts.DependencyBindingType.SINGLETON:
                raise exceptions.CallbackCanBeAttachedToSingletonOnly(
                    instance=callback_record.instance,
                    contract=callback_record.contract
                )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown(exc_type)

    def __iter__(self) -> typing.Generator[contracts.DependencyBindingRecord, None, None]:
        for record in itertools.chain(self._bindings.values(), self._callbacks):
            yield record
