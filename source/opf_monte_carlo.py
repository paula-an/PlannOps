import numpy as np
from basics.powersystem import PowerSystemData
from opf_basic import OPFBasic
from basics.readsystems import read_from_MATPOWER
from basics.powersystem import PowerSystemData
from basics.progress_bar_range import ProgressBarRange
from methodtools import lru_cache
import pyomo.environ as pyo
import numpy as np
from basics.printing import print_centered_text, int_format, float_format, table_format, pyo_extract


class OPFMonteCarlo(OPFBasic):
    def __init__(self, psd: PowerSystemData, ctg_list: np.ndarray=None, MAX_ITER: int=100000, BETA_TOL: float=0.05) -> dict:
        super().__init__(psd)

        # Monte Carlo Parameters
        self.MAX_ITER = MAX_ITER
        self.BETA_TOL = BETA_TOL

        if ctg_list is None:
            self.ctg_list  = np.copy(self.psd.ebranch.set_all)
        else:
            self.ctg_list = ctg_list
        self.ctg_list_len = len(self.ctg_list)

        # Beta history
        self.beta = np.ones(self.MAX_ITER)
    
    def solve_model(self) -> None:

        # Initial mutable data
        ebranch_flow_max_0 = np.copy(self.psd.ebranch.flow_max)
        ebranch_b_lin_0 = np.copy(self.psd.ebranch.b_lin)
        gen_pg_max_0 = np.copy(self.psd.gen.pg_max)

        # Auxiliary reliability indexes
        sumLOLP = 0
        sumEPNS = 0
        sum2EPNS = 0

        pbr = ProgressBarRange(start=1, stop=self.BETA_TOL, mode="log")

        print("\n\nRunning Monte Carlo Simulation...")
        pbar = pbr.start_progess_bar()
        for iter in range(1, self.MAX_ITER+1):

            for k in self.ctg_list:
                self.model.ebranch_flow_max[k] = ebranch_flow_max_0[k]
                self.model.ebranch_b_lin[k] = ebranch_b_lin_0[k]
            for g in self.psd.gen.set_all:
                self.model.gen_pg_max[g] = gen_pg_max_0[g]
            
            # Applying contingencies in existent lines
            ctg_lines = np.zeros(self.ctg_list_len, dtype=int)
            for k in self.ctg_list:
                for _ in range(self.psd.ebranch.nlines[k]):
                    if np.random.rand() < self.psd.ebranch.FOR[k]:
                        ctg_lines[k] += 1
                
                if ctg_lines[k] == 0:
                    continue
                
                remaining_lines = self.psd.ebranch.nlines[k] - ctg_lines[k]
                if remaining_lines > 0:
                    self.model.ebranch_flow_max[k] = self.model.ebranch_flow_max[k] * remaining_lines / self.psd.ebranch.nlines[k]
                    self.model.ebranch_b_lin[k] = self.model.ebranch_b_lin[k] * remaining_lines / self.psd.ebranch.nlines[k]
                else:
                    self.model.ebranch_flow_max[k] = self.psd.ebranch.flow_max_dumb
                    self.model.ebranch_b_lin[k] = self.psd.ebranch.b_dumb

            # Applying contingencies in generators
            ctg_gen = np.zeros(self.psd.gen.len, dtype=int)
            for g in self.psd.gen.set_all:
                if np.random.rand() < self.psd.gen.FOR[g]:
                    ctg_gen[g] = 1
                    self.model.gen_pg_max[g] = 0
            
            total_sl = self._solve_memo(tuple(np.concatenate((ctg_lines, ctg_gen))))

            # Reliability Indexes
            if total_sl > 0:
                sumLOLP += 1
                sumEPNS += total_sl
                sum2EPNS += total_sl**2
        
            self.LOLP = sumLOLP / (iter)
            self.EPNS = sumEPNS / (iter)

            if iter > 1 and self.LOLP > 0:
                var_LOLP = (sumLOLP - iter * self.LOLP**2)/(iter*(iter-1))
                var_EPNS = (sum2EPNS - iter * self.EPNS**2)/(iter*(iter-1))
                b_LOLP = np.sqrt(var_LOLP) / self.LOLP
                b_EPNS = np.sqrt(var_EPNS) / self.EPNS
                
                self.beta[iter-1] = max(b_LOLP, b_EPNS)
                if self.beta[iter-1] > 1:
                    self.beta[iter-1] = 1
                
                # print("{:6}{:6.2f}{:6.1f}".format(iter, total_sl, 100*self.beta[iter-1]))

                if iter>100 and self.beta[iter-1] < self.BETA_TOL:
                    break
                
                pbar.update(pbr.delta(self.beta[iter-1]))
        pbar.close()
    
    @lru_cache(maxsize=1000)
    def _solve_memo(self, ctg_lines):
        super().solve_model()
        sl = pyo_extract(self.model.sl, self.psd.bus.set_with_demand)
        return sum(sl)
    
    def get_results(self, export: bool = True, display: bool = True, file_name: str = "source/.results/results.txt", name_file_test: str = None) -> None:
        super().get_results(export, display, file_name, name_file_test)

        print("\n\n")
        print("Reliability Indexes")
        print("LOLP: {:>.2f} %".format(100 * self.LOLP))
        print("LOLE: {:>.2f} h/yr".format(8760 * self.LOLP))
        print("EPNS: {:>.2f} MW".format(self.psd.power_base * self.LOLP))
        print("EENS: {:>.2f} GWh/yr".format(8.760 * self.psd.power_base * self.LOLP))

        self.results["LOLP"] = self.LOLP
        self.results["EPNS"] = self.EPNS

        if name_file_test is not None:
            np.save(name_file_test, self.results)

def main_opf_monte_carlo(data_file: str, name_file_test: str=None) -> None:
    np.random.seed(seed=0)
    system_data = read_from_MATPOWER(data_file)
    psd = PowerSystemData(system_data=system_data)
    psd.bus.pd_max = psd.bus.pd_max*2
    psd.gen.pg_max = psd.gen.pg_max*2
    op = OPFMonteCarlo(psd=psd)
    op.define_model(debug=False)
    op.solve_model()
    op.get_results(name_file_test=name_file_test)
    return op.results

if __name__ == "__main__":
    # data_file = "source/data/matpower/case3_Basics.m"
    data_file = "source/data/matpower/case24_ieee_rts_reliability.m"
    
    is_for_testing = False
    if is_for_testing:
        name_file_test = "source/tests/results/res_OPFMonteCarlo_case24_ieee_rts_reliability.npy"
        main_opf_monte_carlo(data_file=data_file, name_file_test=name_file_test)
    else:
        main_opf_monte_carlo(data_file=data_file)
        