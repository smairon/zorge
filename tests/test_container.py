import pytest

import zorge
from .definitions import contracts, implementations


def test_callable_dependency_adding(container: zorge.Container):
    container.register_dependency(
        contract=contracts.DBEngineContract,
        implementation=implementations.sync_engine,
        cache_scope='container'
    )

    unit = next(iter(container))
    assert unit.cache_scope == zorge.definition.contracts.CacheScope.CONTAINER
    assert unit.contract is contracts.DBEngineContract
    assert unit.execution_signature is not None
    assert unit.implementation_execution_trigger is None
    assert unit.implementation_execution_type == zorge.definition.contracts.ImplementationExecutionType.SYNC
    assert unit.implementation_kind == zorge.definition.contracts.ImplementationKind.CALLABLE
    assert unit.init_signature is None
    assert unit.implementation() == 'postgresql'


@pytest.mark.asyncio
async def test_async_dependency_adding(container: zorge.Container):
    container.register_dependency(
        contract=contracts.DBEngineContract,
        implementation=implementations.async_engine,
        cache_scope='container'
    )

    unit = next(iter(container))
    assert unit.cache_scope == zorge.definition.contracts.CacheScope.CONTAINER
    assert unit.contract is contracts.DBEngineContract
    assert unit.execution_signature is not None
    assert unit.implementation_execution_trigger is None
    assert unit.implementation_execution_type == zorge.definition.contracts.ImplementationExecutionType.ASYNC
    assert unit.implementation_kind == zorge.definition.contracts.ImplementationKind.CALLABLE
    assert unit.init_signature is None
    assert await unit.implementation() == 'postgresql'


def test_class_dependency_adding(container: zorge.Container):
    container.register_dependency(
        contract=contracts.DBConnectionContract,
        implementation=implementations.DBConnection,
        cache_scope='resolver'
    )

    unit = next(iter(container))
    assert unit.cache_scope == zorge.definition.contracts.CacheScope.RESOLVER
    assert unit.contract is contracts.DBConnectionContract
    assert unit.execution_signature is None
    assert unit.implementation_execution_trigger is None
    assert unit.implementation_execution_type == zorge.definition.contracts.ImplementationExecutionType.SYNC
    assert unit.implementation_kind == zorge.definition.contracts.ImplementationKind.CLASS
    assert type(unit.init_signature) is zorge.definition.contracts.FunctionSignature
    assert unit.init_signature.parameters['db_engine'].type == contracts.DBEngineContract
    assert unit.implementation is implementations.DBConnection
