import pytest
import itertools
from zorge.di import DependencyContainer
from zorge import exceptions
from .contracts import ServiceContract, StorageContract


@pytest.mark.asyncio
async def test_resolving(contractual_service, singleton_instance_storage):
    async with DependencyContainer(bindings=(contractual_service, singleton_instance_storage)) as container:
        async with container.get_provider() as provider:
            service = await provider.get(ServiceContract)
    assert service['a'] == 1


@pytest.mark.asyncio
async def test_instance_identity(contractual_service, singleton_instance_storage):
    async with DependencyContainer(bindings=(contractual_service, singleton_instance_storage)) as container:
        async with container.get_provider() as provider:
            service1 = await provider.get(ServiceContract)
            service2 = await provider.get(ServiceContract)
        async with container.get_provider() as provider:
            service3 = await provider.get(ServiceContract)
    assert service1.get_storage() is service2.get_storage()
    assert service3.get_storage() is not service1.get_storage()
    assert service3.get_storage() is not service2.get_storage()


@pytest.mark.asyncio
async def test_application_identity(contractual_service, singleton_application_storage):
    async with DependencyContainer(bindings=(contractual_service, singleton_application_storage)) as container:
        async with container.get_provider() as provider:
            service1 = await provider.get(ServiceContract)
        async with container.get_provider() as provider:
            service2 = await provider.get(ServiceContract)
    assert service1.get_storage() is service2.get_storage()


@pytest.mark.asyncio
async def test_callbacks(contractual_service, singleton_instance_storage, callbacks):
    async with DependencyContainer(
        bindings=(record for record in itertools.chain((contractual_service, singleton_instance_storage), callbacks))
    ) as container:
        async with container.get_provider() as provider:
            service = await provider.get(ServiceContract)
            assert service.get_storage().is_connection_established()
        assert service.get_storage().is_connection_closed()


@pytest.mark.asyncio
async def test_literals_acceptance(contractual_service, singleton_distributed_storage, literals):
    async with DependencyContainer(
        bindings=(contractual_service, singleton_distributed_storage, literals)
    ) as container:
        async with container.get_provider() as provider:
            service = await provider.get(ServiceContract)
    assert service.get_connection_pool() == 5


@pytest.mark.asyncio
async def test_literals_absence(contractual_service, singleton_distributed_storage):
    with pytest.raises(exceptions.CannotResolveParams):
        async with DependencyContainer(
            bindings=(contractual_service, singleton_distributed_storage)
        ) as container:
            async with container.get_provider() as provider:
                await provider.get(ServiceContract)


@pytest.mark.asyncio
async def test_singleton_context(contractual_service, singleton_distributed_storage, literals):
    with pytest.raises(exceptions.CannotPassContextToSingleton):
        async with DependencyContainer(
            bindings=(contractual_service, singleton_distributed_storage, literals)
        ) as container:
            async with container.get_provider() as provider:
                await provider.get(ServiceContract, context={
                    StorageContract: {
                        'connection_pool': 4
                    }
                })


@pytest.mark.asyncio
async def test_contractual_context(contractual_service, singleton_distributed_storage, literals):
    async with DependencyContainer(
        bindings=(contractual_service, singleton_distributed_storage, literals)
    ) as container:
        async with container.get_provider() as provider:
            service = await provider.get(ServiceContract, context={
                ServiceContract: {
                    'feature_flag': True
                }
            })
            assert service.is_feature_enabled()
