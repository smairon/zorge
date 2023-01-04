import inspect
import typing

from .. import contracts


async def success_shutdown_instance(
    callback_function,
    instance: contracts.SingletonInstance
):
    if not instance:
        return
    if inspect.iscoroutinefunction(callback_function):
        await callback_function(instance)
    elif callable(callback_function):
        callback_function(instance)


async def failure_shutdown_instance(
    callback_function,
    instance: contracts.SingletonInstance,
    exc_type: typing.Any
):
    if not instance:
        return
    if inspect.iscoroutinefunction(callback_function):
        await callback_function(instance, exc_type)
    elif callable(callback_function):
        callback_function(instance, exc_type)
