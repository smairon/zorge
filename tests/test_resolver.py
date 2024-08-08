import pytest

import zorge
from .definitions import contracts, implementations


@pytest.mark.asyncio
async def test_deep_resolving(container: zorge.Container):
    container.register_dependency(
        contract=contracts.DBEngineContract,
        implementation=implementations.async_engine,
        cache_scope='container'
    )
    container.register_dependency(
        contract=contracts.DBConnectionContract,
        implementation=implementations.DBConnection,
        cache_scope='resolver'
    )
    container.register_dependency(
        contract=contracts.UsersRepositoryContract,
        implementation=implementations.UsersRepository,
        cache_scope='resolver'
    )
    container.register_dependency(
        contract=contracts.PostsRepositoryContract,
        implementation=implementations.PostsRepository,
        cache_scope='resolver'
    )
    container.register_dependency(
        contract=contracts.UnitOfWorkContract,
        implementation=implementations.UnitOfWork,
        cache_scope='resolver'
    )

    async with container.get_resolver() as resolver:
        uow = await resolver.resolve(contracts.UnitOfWorkContract)
        assert uow.do() == (
            'UsersRepository using Connection with postgresql',
            'PostsRepository using Connection with postgresql'
        )


@pytest.mark.asyncio
async def test_resolver_cache_scope(container: zorge.Container):
    container.register_dependency(
        contract=contracts.DBEngineContract,
        implementation=implementations.async_engine,
        cache_scope='container'
    )
    container.register_dependency(
        contract=contracts.DBConnectionContract,
        implementation=implementations.DBConnection,
        cache_scope='resolver'
    )

    async with container.get_resolver() as resolver:
        connection1 = await resolver.resolve(contracts.DBConnectionContract)

    async with container.get_resolver() as resolver:
        connection2 = await resolver.resolve(contracts.DBConnectionContract)

    assert connection1 is not connection2


@pytest.mark.asyncio
async def test_container_cache_scope(container: zorge.Container):
    container.register_dependency(
        contract=contracts.DBEngineContract,
        implementation=implementations.async_engine,
        cache_scope='container'
    )
    container.register_dependency(
        contract=contracts.DBConnectionContract,
        implementation=implementations.DBConnection,
        cache_scope='container'
    )

    async with container.get_resolver() as resolver:
        connection1 = await resolver.resolve(contracts.DBConnectionContract)

    async with container.get_resolver() as resolver:
        connection2 = await resolver.resolve(contracts.DBConnectionContract)

    assert connection1 is connection2


@pytest.mark.asyncio
async def test_callback(container: zorge.Container):
    sentinel = 1
    container.register_dependency(
        contract=contracts.DBEngineContract,
        implementation=implementations.async_engine,
        cache_scope='container'
    )
    container.register_dependency(
        contract=contracts.DBConnectionContract,
        implementation=implementations.DBConnection,
        cache_scope='resolver'
    )
    container.register_callback(
        contract=contracts.DBConnectionContract,
        callback=implementations.close_connection,
        trigger='shutdown'
    )

    async with container.get_resolver() as resolver:
        connection = await resolver.resolve(contracts.DBConnectionContract)

    assert connection.sentinel == sentinel


@pytest.mark.asyncio
async def test_resolver_context(container: zorge.Container):
    container.register_dependency(
        contract=contracts.UserActorContract,
        implementation=implementations.UserActor,
        cache_scope='resolver'
    )
    container.register_dependency(
        contract=contracts.PostActorContract,
        implementation=implementations.PostActor,
        cache_scope='resolver'
    )
    container.register_dependency(
        contract=contracts.UserServiceContract,
        implementation=implementations.UserService,
        cache_scope='resolver'
    )

    async with container.get_resolver(
        contracts.UserContextContract(user_id=1),
        {contracts.PoolSizeContract: 1}
    ) as resolver:
        service = await resolver.resolve(contracts.UserServiceContract)
        assert service.get_ids() == [1, 1, 1]
