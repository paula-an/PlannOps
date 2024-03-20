from tqdm import tqdm
import numpy as np

class ProgressBarRange():
    def __init__(self, start: int, stop: int, mode: str="lin") -> None:
        self.start = start
        self.stop = stop
        self.mode = mode
        self.range = self._create_range()
        self.place = 0

    def _create_range(self):
        if self.mode == "lin":
            return np.linspace(start=self.start, stop=self.stop, num=20)
        elif self.mode == "log":
            return np.geomspace(start=self.start, stop=self.stop, num=20)
        
    def start_progess_bar(self):
        return tqdm(total = 100)
    
    def delta(self, value: float):
        if value < self.stop:
            return 0
        new_place = np.where(value>=self.range)[0][0]
        delta = (new_place - self.place)*100/20
        self.place = np.copy(new_place)
        return delta
    

