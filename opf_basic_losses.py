from basics.printing import pyo_extract
from opf_basic import OPFBasic
from abc_classes.optimization import PowerSystemData
from basics.readsystems import read_from_MATPOWER
import pyomo.environ as pyo
import numpy as np

class OPFBasicLoss(OPFBasic):

    def __init__(self, psd: PowerSystemData, MAX_ITER: int = 4, TOL: float = 1e-8,) -> None:
        super().__init__(psd)

        self.MAX_ITER = MAX_ITER
        self.TOL = TOL

        self.pd_max0 = np.copy(self.psd.bus.pd_max)

    def solve_model(self) -> None:
        for iter in range(self.MAX_ITER):
            print("... iter:", iter+1)
            
            super().solve_model()

            # Adding losses to demands
            self.pd_max_old = np.copy(self.psd.bus.pd_max)
            self.psd.bus.pd_max = np.copy(self.pd_max0)

            th = pyo_extract(self.model.th, self.psd.bus.set_all)
            for k in self.psd.ebranch.set_all:
                
                ki = self.psd.ebranch.bus_fr[k]
                kj = self.psd.ebranch.bus_to[k]
                self.losses[k] = 0.5 * self.psd.ebranch.g[k]*(th[ki]-th[kj])**2

                self.psd.bus.pd_max[ki] += 0.5*self.losses[k]
                self.psd.bus.pd_max[kj] += 0.5*self.losses[k]

            # Stop criterion
            if np.sum((self.psd.bus.pd_max-self.pd_max_old)**2) < self.TOL:
                return

            self.define_model(debug=True)  # It can be optimized


def main():
    file_name = "dataMATPOWER/case3.m"
    system_data = read_from_MATPOWER(file_name)
    psd = PowerSystemData(system_data=system_data)
    op = OPFBasicLoss(psd)
    op.define_model(debug=True)
    op.solve_model()
    op.get_results()

if __name__ == "__main__":
    main()