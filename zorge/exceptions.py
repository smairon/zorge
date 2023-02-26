from .contracts import DependencyBindingContract, DependencyBindingInstance


class ZorgeException(Exception):
    def __init__(
        self,
        instance: DependencyBindingInstance,
        contract: DependencyBindingContract,
        message: str | None = None,
    ):
        self.instance = instance
        self.contract = contract
        if not message:
            message = 'Undefined error'
        super().__init__(message)


class ContractNotRegistered(ZorgeException):
    def __init__(
        self,
        contract: DependencyBindingContract,
    ):
        super().__init__(
            instance=None,
            contract=contract,
            message=f'Contract {contract} not registered'
        )


class ContractNotDefined(ZorgeException):
    def __init__(
        self,
        instance: DependencyBindingInstance,
        contract: DependencyBindingContract,
    ):
        super().__init__(
            instance=instance,
            contract=contract,
            message=f'Contract for instance {type(instance)} not defined'
        )


class CallbackInstanceMustBeCallable(ZorgeException):
    def __init__(
        self,
        instance: DependencyBindingInstance,
        contract: DependencyBindingContract,
    ):
        super().__init__(
            instance=instance,
            contract=contract,
            message=f'Callback instance for contract {contract.__class__} must be callable'
        )


class LiteralMustBeMapping(ZorgeException):
    def __init__(
        self,
        instance: DependencyBindingInstance
    ):
        super().__init__(
            instance=instance,
            contract=type(instance),
            message=f'Literal instance {type(instance).__class__} must be mapping'
        )


class CallbackCanBeAttachedToSingletonOnly(ZorgeException):
    def __init__(
        self,
        instance: DependencyBindingInstance,
        contract: DependencyBindingContract,
    ):
        super().__init__(
            instance=instance,
            contract=contract,
            message=f'Callback can be attached to singleton. Not satisfied for {contract}'
        )


class CannotResolveParams(ZorgeException):
    def __init__(
        self,
        contract: DependencyBindingContract,
        message: str
    ):
        super().__init__(
            instance=None,
            contract=contract,
            message=message
        )


class CannotPassContextToSingleton(ZorgeException):
    def __init__(
        self,
        contract: DependencyBindingContract
    ):
        super().__init__(
            instance=None,
            contract=contract,
            message=f'Cannot pass context to singleton {contract}. You can use contractual binding type instead'
        )
