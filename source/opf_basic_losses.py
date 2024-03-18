from basics.printing import pyo_extract
from opf_basic import OPFBasic
from abc_classes.optimization import PowerSystemData
from basics.readsystems import read_from_MATPOWER
import numpy as np

class OPFBasicLoss(OPFBasic):

    def __init__(self, psd: PowerSystemData, MAX_ITER: int = 4, TOL: float = 1e-8,) -> None:
        super().__init__(psd)

        self.MAX_ITER = MAX_ITER
        self.TOL = TOL

        self.pd_max0 = np.copy(self.psd.bus.pd_max)

        # For this class, all buses have demand
        self.psd.bus.define_all_as_demand()

    def solve_model(self) -> None:
        for iter in range(self.MAX_ITER):
            print("... iter:", iter+1)
            
            super().solve_model()

            self._update_pd_max()

            if self._stop_criterion():
                return

            # with open('output.txt', 'w') as file:
            #     self.model.pprint(ostream=file)

    def _update_pd_max(self) -> None:
        self.pd_max_old = np.copy(self.psd.bus.pd_max)
        self.psd.bus.pd_max = np.copy(self.pd_max0)

        th = pyo_extract(self.model.th, self.psd.bus.set_all)
        for k in self.psd.ebranch.set_all:
            
            ki = self.psd.ebranch.bus_fr[k]
            kj = self.psd.ebranch.bus_to[k]
            self.losses[k] = 0.5 * self.psd.ebranch.g[k]*(th[ki]-th[kj])**2

            self.psd.bus.pd_max[ki] += 0.5*self.losses[k]
            self.psd.bus.pd_max[kj] += 0.5*self.losses[k]
        
        for b in self.psd.bus.set_all:
            self.model.bus_pd_max[b] = self.psd.bus.pd_max[b]

    def _stop_criterion(self) -> bool:
        return np.sum((self.psd.bus.pd_max-self.pd_max_old)**2) < self.TOL

def main_opf_basic_losses(data_file: str, name_file_test: str=None) -> None:
    system_data = read_from_MATPOWER(data_file)
    psd = PowerSystemData(system_data=system_data)
    op = OPFBasicLoss(psd)
    op.define_model(debug=True)
    op.solve_model()
    op.get_results(name_file_test=name_file_test)
    return op.results

if __name__ == "__main__":
    data_file = "source/tests/data/MATPOWER/case3.m"

    is_for_testing = True
    if is_for_testing:
        name_file_test = "source/tests/results/res_OPFBasic_loss_case3.npy"
        main_opf_basic_losses(data_file=data_file, name_file_test=name_file_test)
    else:
        main_opf_basic_losses(data_file=data_file)
