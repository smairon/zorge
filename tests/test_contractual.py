import pytest
import itertools
from zorge.di import DependencyContainer
from zorge import exceptions
from .contracts import ServiceContract, StorageContract


@pytest.mark.asyncio
async def test_resolving(contractual_service, contractual_db_storage):
    async with DependencyContainer(bindings=(contractual_service, contractual_db_storage)) as container:
        async with container.get_provider() as provider:
            service = await provider.get(ServiceContract)
    assert service['a'] == 1


@pytest.mark.asyncio
async def test_distinct_of_instances(contractual_service, contractual_db_storage):
    async with DependencyContainer(bindings=(contractual_service, contractual_db_storage)) as container:
        async with container.get_provider() as provider:
            service1 = await provider.get(ServiceContract)
            service2 = await provider.get(ServiceContract)
    assert id(service1) != id(service2)
    assert service1.get_storage() is not service2.get_storage()


@pytest.mark.asyncio
async def test_callbacks(contractual_service, contractual_db_storage, callbacks):
    with pytest.raises(exceptions.CallbackCanBeAttachedToSingletonOnly):
        async with DependencyContainer(
            bindings=(record for record in itertools.chain((contractual_service, contractual_db_storage), callbacks))
        ) as container:
            async with container.get_provider() as provider:
                await provider.get(ServiceContract)


@pytest.mark.asyncio
async def test_literals_acceptance(contractual_service, contractual_distributed_storage, literals):
    async with DependencyContainer(
        bindings=(contractual_service, contractual_distributed_storage, literals)
    ) as container:
        async with container.get_provider() as provider:
            service = await provider.get(ServiceContract)
    assert service.get_connection_pool() == 5
    assert service.is_feature_enabled() is False


@pytest.mark.asyncio
async def test_literals_absence(contractual_service, contractual_distributed_storage):
    with pytest.raises(exceptions.CannotResolveParams):
        async with DependencyContainer(
            bindings=(contractual_service, contractual_distributed_storage)
        ) as container:
            async with container.get_provider() as provider:
                await provider.get(ServiceContract)


@pytest.mark.asyncio
async def test_context(contractual_service, contractual_distributed_storage, literals):
    async with DependencyContainer(
        bindings=(contractual_service, contractual_distributed_storage, literals)
    ) as container:
        async with container.get_provider() as provider:
            service = await provider.get(ServiceContract, context={
                StorageContract: {
                    'connection_pool': 4
                },
                ServiceContract: {
                    'feature_flag': True
                }
            })
    assert service.get_connection_pool() == 4
    assert service.is_feature_enabled()
