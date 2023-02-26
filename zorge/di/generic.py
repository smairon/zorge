import inspect
import typing

from .. import contracts


async def startup(
    dependency_provider: contracts.DependencyProvider,
) -> typing.NoReturn:
    for record in dependency_provider:
        if record.binding_type == contracts.DependencyBindingType.ON_STARTUP_CALLBACK:
            instance = dependency_provider.get_registry().get(record.contract)
            if not instance:
                instance = await dependency_provider.get(record.contract)
            if instance:
                await _evoke_callback(
                    callback_function=record.instance,
                    instance=instance
                )


async def shutdown(
    dependency_space: contracts.DependencyProvider | contracts.DependencyContainer,
    exc_type: typing.Any,
    scope: contracts.DependencyBindingScope
) -> typing.NoReturn:
    _callback_types = {
        True: contracts.DependencyBindingType.ON_SHUTDOWN_FAILURE_CALLBACK,
        False: contracts.DependencyBindingType.ON_SHUTDOWN_SUCCESS_CALLBACK
    }
    for record in dependency_space:
        if (
            record.scope == scope
            and
            record.binding_type == _callback_types.get(bool(exc_type))
        ):
            params = dict(
                callback_function=record.instance,
                instance=dependency_space.get_registry().get(record.contract)
            )
            if bool(exc_type):
                params['exc_type'] = exc_type
            await _evoke_callback(**params)


async def _evoke_callback(
    callback_function,
    instance: contracts.SingletonInstance,
    exc_type: typing.Any = contracts.NotDefined
):
    if not instance:
        return
    if inspect.iscoroutinefunction(callback_function):
        if exc_type is contracts.NotDefined:
            await callback_function(instance)
        else:
            await callback_function(instance, exc_type)
    elif callable(callback_function):
        if exc_type is contracts.NotDefined:
            callback_function(instance)
        else:
            callback_function(instance, exc_type)
