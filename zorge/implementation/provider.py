import collections.abc
import types
import inspect
import typing

import zorge


class ContainerProvider:
    def __init__(
        self,
        **config
    ):
        self._config = config
        self._container = zorge.Container()

    def load_module(self, module: types.ModuleType) -> typing.Self:
        self._container += self._assemble(module)
        return self

    def get_container(self) -> zorge.Container:
        return self._container

    def _assemble(
        self,
        module: types.ModuleType
    ) -> zorge.Container:
        container = zorge.Container()
        for e in inspect.getmembers(module):
            entity = e[1]
            if inspect.ismodule(entity) and module.__name__ in entity.__name__:
                container += self._assemble(entity)
            elif inspect.isfunction(entity) and entity.__name__.endswith('_dc'):
                container += entity(**self._derive_parameters(entity))
        return container

    def _derive_parameters(self, entity: collections.abc.Callable):
        signature = inspect.signature(entity)
        params = {}
        for p in signature.parameters.values():
            if p.name in self._config:
                params[p.name] = self._config[p.name]
            else:
                raise NotImplementedError(f"Parameter {p.name} not defined for container {entity.__name__}")
        return params
