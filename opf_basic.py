# Created in 05/03/2024 by Arthur

from basics.readsystems import read_from_MATPOWER
from basics.powersystem import PowerSystemData
from abc_classes.optimization import OptimizationProblem
import pyomo.environ as pyo
import numpy as np
from basics.printing import print_centered_text, int_format, float_format, table_format
import sys

class OPFBasic(OptimizationProblem):

    def __init__(self, psd: PowerSystemData) -> None:
        # PowerSystemData injection
        self.psd = psd
        
        self.losses = np.zeros(self.psd.ebranch.len)
    
    def define_model(self, debug: bool = False):
        # Model
        self.model = pyo.ConcreteModel(name=self.__class__.__name__)

        # Mutable Parameters
        self.model.bus_pd_max = pyo.Param(self.psd.bus.set_all, initialize=self.psd.bus.pd_max, mutable=True)

        # Variables
        self.model.pg = pyo.Var(self.psd.gen.set_all, within=pyo.Reals, bounds=self._bounds_pg)  # Power Generation
        self.model.th = pyo.Var(self.psd.bus.set_all, within=pyo.Reals, bounds=(-np.pi, np.pi))  # Voltage angle
        self.model.th[0].fix(0)
        self.model.sl = pyo.Var(self.psd.bus.set_with_demand, within=pyo.Reals, bounds=self._bounds_sl)  # Load shedding
        
        # Dependent variables
        self.model.pf = pyo.Var(self.psd.ebranch.set_all, within=pyo.Reals, bounds=self._bounds_pf)  # Active Power Flow

        # Objective
        self.model.obj = pyo.Objective(expr=self._create_objective())

        # Constraints
        self.model.con_power_balance = pyo.Constraint(self.psd.bus.set_all, rule=self._rule_power_balance)
        self.model.con_power_flow = pyo.Constraint(self.psd.ebranch.set_all, rule=self._rule_power_flow)

        # Data file for debug
        if debug:
            with open('output.txt', 'w') as file:
                self.model.pprint(ostream=file)
    
    def solve_model(self) -> None:
        solver = pyo.SolverFactory('glpk')
        solver.solve(self.model)
    
    def _bounds_pf(self, _, k: int) -> tuple:
        return (-self.psd.ebranch.flow_max[k], +self.psd.ebranch.flow_max[k])
    
    def _bounds_pg(self, _, g: int) -> tuple:
        return (0, self.psd.gen.pg_max[g])
    
    def _bounds_sl(self, _, b: int) -> tuple:
        return (0, self.model.bus_pd_max[b])
    
    def _create_objective(self) -> pyo.Expression:
        return self._total_pg_cost()+self._total_sl_cost()
    
    def _pf_inj(self, b: int) -> pyo.Expression:
        pf_inj = 0
        for k in np.where(self.psd.ebranch.bus_fr == b)[0]:
            pf_inj += self.model.pf[k]
        for k in np.where(self.psd.ebranch.bus_to == b)[0]:
            pf_inj -= self.model.pf[k]
        return pf_inj
    
    def _pg_inj(self, b: int) -> pyo.Expression:
        pg_inj = 0
        for g in np.where(self.psd.gen.bus == b)[0]:
            pg_inj += self.model.pg[g]
        return pg_inj
    
    def _rule_power_balance(self, _, b: int) -> pyo.Expression:
        return self._pg_inj(b)-self._pf_inj(b)+self._sl_inj(b) == self.model.bus_pd_max[b]
    
    def _rule_power_flow(self, _, k: int) -> pyo.Expression:
        ki = self.psd.ebranch.bus_fr[k]
        kj = self.psd.ebranch.bus_to[k]
        return self.model.pf[k] == self.psd.ebranch.b_lin[k]*(self.model.th[ki]-self.model.th[kj])
    
    def _sl_inj(self, b: int):
        if b in self.psd.bus.set_with_demand:
            return self.model.sl[b]
        return 0
    
    def _total_pg_cost(self) -> pyo.Expression:
        return sum([self.psd.gen.cost[g]*self.model.pg[g] for g in self.psd.gen.set_all])
    
    def _total_sl_cost(self) -> pyo.Expression:
        return sum([self.psd.bus.sl_cost*self.model.sl[b] for b in self.psd.bus.set_with_demand])
    
    def get_results(self, export: bool=True, display: bool=True, file_name: str="results.txt") -> None:
        with open(file_name, "w") as file:
            for idx, out in enumerate([sys.stdout, file]):
                if idx == 0 and not display:
                    continue
                if idx == 1 and not export:
                    continue
                print("-----------------------------------------", file=out)
                print("-----------------Results-----------------", file=out)
                print("-----------------------------------------", file=out)

                print("\n\n", file=out)
                ncol = 4
                print_centered_text("Bus data", file=out, ncol=ncol)
                print(table_format(ncol=ncol).format("Bus", "pg", "LShed", "Angle"), file=out)
                for b in self.psd.bus.set_all:
                    bus = int_format(b+1)
                    gen = float_format(self._pg_inj(b))
                    lshed = float_format(self._sl_inj(b))
                    angle = float_format(self.model.th[b])
                    print(bus + gen + lshed + angle, file=out)
                
                print("\n\n", file=out)
                ncol = 5
                print_centered_text("Existent branch data", file=out, ncol=ncol)
                print(table_format(ncol=ncol).format("Branch", "fr", "to", "pflow", "losses"), file=out)
                for k in self.psd.ebranch.set_all:
                    branch = int_format(k+1)
                    fr = int_format(self.psd.ebranch.bus_fr[k]+1)
                    to = int_format(self.psd.ebranch.bus_to[k]+1)
                    pflow = float_format(self.model.pf[k])
                    losses = float_format(self.losses[k])
                    print(branch + fr + to + pflow + losses, file=out)
                
                print("\n\n", file=out)
                ncol = 4
                print_centered_text("Generation data", file=out, ncol=ncol)
                print(table_format(ncol=ncol).format("Gen", "Bus", "pg", "cost"), file=out)
                for g in self.psd.gen.set_all:
                    gen = int_format(g+1)
                    bus = int_format(self.psd.gen.bus[g]+1)
                    pg = float_format(self.model.pg[g])
                    cost = float_format(self.model.pg[g]*self.psd.gen.cost[g])
                    print(gen + bus + pg + cost, file=out)

                print("\nObjective:", file=out)
                print(pyo.value(self.model.obj), file=out)

                print("\nTotal Power generation cost:", file=out)
                print(pyo.value(self._total_pg_cost()), file=out)

                print("\nTotal Load shedding cost:", file=out)
                print(pyo.value(self._total_sl_cost()), file=out)

def main():
    data_file = "dataMATPOWER/case3.m"
    system_data = read_from_MATPOWER(data_file)
    psd = PowerSystemData(system_data=system_data)
    op = OPFBasic(psd)
    op.define_model(debug=True)
    op.solve_model()
    op.get_results()

if __name__ == "__main__":
    main()
        