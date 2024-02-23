from abc import abstractmethod, ABC
from powersystem import PowerSystemData

class OptimizationProblem(ABC):
    
    @abstractmethod
    def __init__(self, psd: PowerSystemData) -> None:
        ...
    
    @abstractmethod
    def define_model(self, debug: bool = False):
        ...

    @abstractmethod
    def solve_model(self):
        ...
