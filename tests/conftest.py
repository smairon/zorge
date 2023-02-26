import pytest
from zorge.contracts import DependencyBindingRecord, DependencyBindingType, DependencyBindingScope
from .contracts import StorageContract, ServiceContract


class Storage(StorageContract):
    def __init__(self):
        self._data = {'a': 1}
        self._connection = None

    def __getitem__(self, item):
        return self._data[item]

    def shutdown(self):
        self._connection = False

    def startup(self):
        self._connection = True

    def is_connection_closed(self):
        return self._connection is False

    def is_connection_established(self):
        return self._connection is True

    def get_connection_pool(self) -> int:
        raise NotImplemented


class DBStorage(Storage):
    pass


class RAMStorage(Storage):
    pass


class DistributedStorage(Storage):
    def __init__(self, connection_pool: int):
        self._connection_pool = connection_pool
        super().__init__()

    def get_connection_pool(self):
        return self._connection_pool


class Service(ServiceContract):
    def __init__(self, storage: StorageContract, feature_flag: bool = False):
        self._storage = storage
        self._feature_flag = feature_flag

    def __getitem__(self, item):
        return self._storage[item]

    def get_storage(self):
        return self._storage

    def is_feature_enabled(self) -> bool:
        return self._feature_flag

    def get_connection_pool(self):
        return self._storage.get_connection_pool()


@pytest.fixture()
def callbacks():
    yield (
        DependencyBindingRecord(
            binding_type=DependencyBindingType.ON_SHUTDOWN_SUCCESS_CALLBACK,
            contract=StorageContract,
            instance=lambda x: x.shutdown(),
            scope=DependencyBindingScope.INSTANCE
        ),
        DependencyBindingRecord(
            binding_type=DependencyBindingType.ON_SHUTDOWN_FAILURE_CALLBACK,
            contract=StorageContract,
            instance=lambda x: x.shutdown(),
            scope=DependencyBindingScope.INSTANCE
        ),
        DependencyBindingRecord(
            binding_type=DependencyBindingType.ON_STARTUP_CALLBACK,
            contract=StorageContract,
            instance=lambda x: x.startup(),
            scope=DependencyBindingScope.INSTANCE
        ),
    )


@pytest.fixture()
def literals():
    return DependencyBindingRecord(
        binding_type=DependencyBindingType.LITERAL,
        instance={
            'connection_pool': 5
        },
    )


@pytest.fixture()
def contractual_service():
    return DependencyBindingRecord(
        binding_type=DependencyBindingType.CONTRACTUAL,
        contract=ServiceContract,
        instance=Service
    )


@pytest.fixture()
def contractual_db_storage():
    return DependencyBindingRecord(
        binding_type=DependencyBindingType.CONTRACTUAL,
        contract=StorageContract,
        instance=DBStorage
    )


@pytest.fixture()
def contractual_distributed_storage():
    return DependencyBindingRecord(
        binding_type=DependencyBindingType.CONTRACTUAL,
        contract=StorageContract,
        instance=DistributedStorage
    )


@pytest.fixture()
def singleton_instance_storage():
    yield DependencyBindingRecord(
        binding_type=DependencyBindingType.SINGLETON,
        contract=StorageContract,
        instance=DBStorage,
        scope=DependencyBindingScope.INSTANCE
    )


@pytest.fixture()
def singleton_application_storage():
    yield DependencyBindingRecord(
        binding_type=DependencyBindingType.SINGLETON,
        contract=StorageContract,
        instance=DBStorage,
        scope=DependencyBindingScope.APPLICATION
    )


@pytest.fixture()
def singleton_distributed_storage():
    yield DependencyBindingRecord(
        binding_type=DependencyBindingType.SINGLETON,
        contract=StorageContract,
        instance=DistributedStorage,
        scope=DependencyBindingScope.INSTANCE
    )
