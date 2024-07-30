from abc import ABC, abstractmethod


class ProgressBar(ABC):
    @abstractmethod
    def __init__():
        pass

    @abstractmethod
    def clear(self):
        pass

    @abstractmethod
    def update(self, size: int):
        pass

    @abstractmethod
    def set(self, total: int, num: int = 0):
        pass

    @abstractmethod
    def show(self):
        pass
