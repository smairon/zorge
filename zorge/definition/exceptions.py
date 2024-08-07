import abc


class DIException(Exception):
    def __init__(self, contract: type):
        self.contract = contract
        super().__init__(self.message())

    @abc.abstractmethod
    def message(self):
        pass


class UnsupportedTrigger(DIException):
    def __init__(self, contract: type, trigger: str):
        super().__init__(contract)
        self._trigger = trigger

    def message(self):
        return f'Unsupported trigger: {self._trigger} for contract: {self.contract}'


class ContractIsNotRegistered(DIException):
    def message(self):
        return f'Contract is not registered: {self.contract}'


class CannotAutomaticallyDeriveContract(DIException):
    def message(self):
        return f'Cannot automatically derive contract: {self.contract}'
