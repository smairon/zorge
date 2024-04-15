import abc


class DIException(Exception):
    def __init__(self, contract):
        self.contract = contract
        super().__init__(self.message())

    @abc.abstractmethod
    def message(self):
        pass


class ContractIsNotRegistered(DIException):
    def message(self):
        return f'Contract is not registered: {self.contract}'


class CannotAutomaticallyDeriveContract(DIException):
    def message(self):
        return f'Cannot automatically derive contract: {self.contract}'
