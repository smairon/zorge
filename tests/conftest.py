import pytest
from zorge import Container


@pytest.fixture
def container() -> Container:
    return Container()
