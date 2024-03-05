from abc import abstractmethod, ABC
from basics.powersystem import PowerSystemData

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

    @abstractmethod
    def get_results(self, export: bool=True, display: bool=True, file_name: str="results.txt") -> None:
        ...
