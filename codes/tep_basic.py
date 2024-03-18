# Created in 16/03/2024 by Arthur

from basics.readsystems import read_from_MATPOWER
from basics.powersystem import PowerSystemData
from opf_basic import OPFBasic
import pyomo.environ as pyo
import numpy as np
from basics.printing import print_centered_text, int_format, float_format, table_format, pyo_extract
import sys

class TEPBasic(OPFBasic):

    def __init__(self, psd: PowerSystemData) -> None:
        super().__init__(psd)

        # Load Sheding cost
        self.psd.bus.sl_cost = 100*max(self.psd.xbranch.invT_cost)
    
    def define_model(self, debug: bool = False):
        
        # Variables
        self.model.xpf = pyo.Var(self.psd.xbranch_bin.set_all, within=pyo.Reals, bounds=self._bounds_xpf)  # Power flow in new lines
        self.model.invT = pyo.Var(self.psd.xbranch_bin.set_all, within=pyo.Binary)  # Transmission investment
        
        super().define_model(debug)

        # Disjunctive power flow
        self.model.con_power_xflow_disj_pos = pyo.Constraint(self.psd.xbranch_bin.set_all, rule=self._rule_power_xflow_disj_pos)
        self.model.con_power_xflow_disj_neg = pyo.Constraint(self.psd.xbranch_bin.set_all, rule=self._rule_power_xflow_disj_neg)

        # Power flow limits
        self.model.con_power_xflow_pos = pyo.Constraint(self.psd.xbranch_bin.set_all, rule=self._rule_power_xflow_pos)
        self.model.con_power_xflow_neg = pyo.Constraint(self.psd.xbranch_bin.set_all, rule=self._rule_power_xflow_neg)
        
        # Data file for debug
        if debug:
            with open('codes/.results/output.txt', 'w') as file:
                self.model.pprint(ostream=file)

    def _create_objective(self) -> pyo.Expression:
        return self._total_pg_cost()+self._total_sl_cost()+self._total_invT_cost()
    
    def _xpf_inj(self, b: int) -> pyo.Expression:
        xpf_inj = 0
        for k in np.where(self.psd.xbranch_bin.bus_fr == b)[0]:
            xpf_inj += self.model.xpf[k]
        for k in np.where(self.psd.xbranch_bin.bus_to == b)[0]:
            xpf_inj -= self.model.xpf[k]
        return xpf_inj
    
    def _bounds_xpf(self, _, k: int) -> tuple:
        return (-self.psd.xbranch_bin.flow_max[k], +self.psd.xbranch_bin.flow_max[k])
    
    def _rule_power_balance(self, _, b: int) -> pyo.Expression:
        return self._pg_inj(b)-self._pf_inj(b)-self._xpf_inj(b)+self._sl_inj(b) == self.model.bus_pd_max[b]
    
    def _rule_power_xflow_disj_pos(self, _, k: int) -> pyo.Expression:
        ki = self.psd.xbranch_bin.bus_fr[k]
        kj = self.psd.xbranch_bin.bus_to[k]
        return -self.psd.xbranch_bin.bigM[k] * (1 - self.model.invT[k]) <= self.model.xpf[k] + self.psd.xbranch_bin.b_lin[k]*(self.model.th[ki]-self.model.th[kj])
    
    def _rule_power_xflow_disj_neg(self, _, k: int) -> pyo.Expression:
        ki = self.psd.xbranch_bin.bus_fr[k]
        kj = self.psd.xbranch_bin.bus_to[k]
        return self.model.xpf[k] + self.psd.xbranch_bin.b_lin[k]*(self.model.th[ki]-self.model.th[kj]) <= self.psd.xbranch_bin.bigM[k] * (1 - self.model.invT[k])
    
    def _rule_power_xflow_pos(self, _, k: int) -> pyo.Expression:
        return self.model.xpf[k] <=  self.model.invT[k] * self.psd.xbranch_bin.flow_max[k]
    
    def _rule_power_xflow_neg(self, _, k: int) -> pyo.Expression:
        return -self.model.invT[k] * self.psd.xbranch_bin.flow_max[k] <= self.model.xpf[k]
    
    def _total_invT_cost(self) -> pyo.Expression:
        return sum([self.psd.xbranch_bin.invT_cost[k]*self.model.invT[k] for k in self.psd.xbranch_bin.set_all])
    
    def get_results(self, export: bool=True, display: bool=True, file_name: str="codes/.results/results.txt") -> None:
        super().get_results(export=export, display=display, file_name=file_name)
        with open(file_name, "a") as file:
            for idx, out in enumerate([sys.stdout, file]):
                if idx == 0 and not display:
                    continue
                if idx == 1 and not export:
                    continue
                
                xpf, xlosses, invT = self._get_non_bin_res()
                print("\n\n", file=out)
                ncol = 6
                print_centered_text("Candidate branch data", file=out, ncol=ncol)
                print(table_format(ncol=ncol).format("Branch", "fr", "to", "pflow", "losses", "invT"), file=out)
                for k in self.psd.xbranch.set_all:
                    branch = int_format(k+1)
                    fr = int_format(self.psd.xbranch.bus_fr[k]+1)
                    to = int_format(self.psd.xbranch.bus_to[k]+1)
                    pflow = float_format(xpf[k])
                    losses = float_format(xlosses[k])
                    n_invT = int_format(invT[k])
                    print(branch + fr + to + pflow + losses + n_invT, file=out)
    
    def _get_non_bin_res(self):
        xpf = np.zeros(self.psd.xbranch.len)
        xlosses = np.zeros(self.psd.xbranch.len)
        invT = np.zeros(self.psd.xbranch.len, dtype=int)

        res_xpf = pyo_extract(self.model.xpf, self.psd.xbranch_bin.set_all)
        res_invT = pyo_extract(self.model.invT, self.psd.xbranch_bin.set_all)

        idx = 0
        for k in self.psd.xbranch.set_all:
            for _ in range(self.psd.xbranch.invT_max[k]):
                xpf[k] += res_xpf[idx]
                invT[k] += res_invT[idx]
                idx += 1
        
        return xpf, xlosses, invT

def main():
    data_file = "codes/data/MATPOWER/case3.m"
    system_data = read_from_MATPOWER(data_file)
    psd = PowerSystemData(system_data=system_data)
    op = TEPBasic(psd)
    op.define_model(debug=True)
    op.solve_model()
    op.get_results()

if __name__ == "__main__":
    main()
        