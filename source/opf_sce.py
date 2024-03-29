# Created in 06/03/2024 by Arthur

from basics.readsystems import read_from_MATPOWER
from basics.powersystem import PowerSystemData
from abc_classes.optimization import OptimizationProblem
import pyomo.environ as pyo
import numpy as np
from basics.printing import print_centered_text, int_format, float_format, table_format, pyo_extract_2D
import sys

class OPFSce(OptimizationProblem):

    def __init__(self, psd: PowerSystemData) -> None:
        # PowerSystemData injection
        self.psd = psd
        
        self.losses = np.zeros((self.psd.ebranch.len, self.psd.sce.len_obs))
    
    def define_model(self, debug: bool = False):
        # Model
        self.model = pyo.ConcreteModel(name=self.__class__.__name__)

        # Scenarios' Parameters
        self.model.bus_pd_max = pyo.Param(self.psd.bus.set_all, self.psd.sce.set_obs, initialize=self._init_bus_pd_sce)
        self.model.gen_pg_sce = pyo.Param(self.psd.gen.set_all, self.psd.sce.set_obs, initialize=self._init_bus_pg_sce)
        
        # Variables
        self.model.pg = pyo.Var(self.psd.gen.set_all, self.psd.sce.set_obs, within=pyo.Reals, bounds=self._bounds_pg)  # Power Generation
        self.model.th = pyo.Var(self.psd.bus.set_all, self.psd.sce.set_obs, within=pyo.Reals, bounds=(-np.pi, np.pi))  # Voltage angle
        for s in self.psd.sce.set_obs:  
            self.model.th[0, s].fix(0)
        self.model.sl = pyo.Var(self.psd.bus.set_with_demand, self.psd.sce.set_obs, within=pyo.Reals, bounds=self._bounds_sl)  # Load shedding
        
        # Dependent variables
        self.model.pf = pyo.Var(self.psd.ebranch.set_all, self.psd.sce.set_obs, within=pyo.Reals, bounds=self._bounds_pf)  # Active Power Flow

        # Objective
        self.model.obj = pyo.Objective(expr=self._create_objective())

        # Constraints
        self.model.con_power_balance = pyo.Constraint(self.psd.bus.set_all, self.psd.sce.set_obs, rule=self._rule_power_balance)
        self.model.con_power_flow = pyo.Constraint(self.psd.ebranch.set_all, self.psd.sce.set_obs, rule=self._rule_power_flow)

        # Data file for debug
        if debug:
            with open('source/.results/output.txt', 'w') as file:
                self.model.pprint(ostream=file)
    
    def solve_model(self) -> None:
        solver = pyo.SolverFactory('glpk')
        solver.solve(self.model)

    def _init_bus_pd_sce(self, _, b: int, s: int) -> np.ndarray:
        return self.psd.bus.pd_max[b] * self.psd.sce.data[s, self.psd.bus.area[b]]

    def _init_bus_pg_sce(self, _, g: int, s: int) -> np.ndarray:
        gen_serie = self.psd.gen.serie[g]
        if gen_serie < 0:
            return 1
        else:
            return self.psd.sce.data[s, gen_serie]
    
    def _bounds_pf(self, _, k: int, s: int) -> tuple:
        return (-self.psd.ebranch.flow_max[k], +self.psd.ebranch.flow_max[k])
    
    def _bounds_pg(self, _, g: int, s: int) -> tuple:
        return (0, self.psd.gen.pg_max[g] * self.model.gen_pg_sce[g, s])
    
    def _bounds_sl(self, _, b: int, s: int) -> tuple:
        return (0, self.model.bus_pd_max[b, s])
    
    def _create_objective(self) -> pyo.Expression:
        return self._total_pg_cost()+self._total_sl_cost()
    
    def _pf_inj(self, b: int, s: int) -> pyo.Expression:
        pf_inj = 0
        for k in np.where(self.psd.ebranch.bus_fr == b)[0]:
            pf_inj += self.model.pf[k, s]
        for k in np.where(self.psd.ebranch.bus_to == b)[0]:
            pf_inj -= self.model.pf[k, s]
        return pf_inj
    
    def _pg_inj(self, b: int, s: int) -> pyo.Expression:
        pg_inj = 0
        for g in np.where(self.psd.gen.bus == b)[0]:
            pg_inj += self.model.pg[g, s]
        return pg_inj
    
    def _rule_power_balance(self, _, b: int, s: int) -> pyo.Expression:
        return self._pg_inj(b, s)-self._pf_inj(b, s)+self._sl_inj(b, s) == self.model.bus_pd_max[b, s]
    
    def _rule_power_flow(self, _, k: int, s: int) -> pyo.Expression:
        ki = self.psd.ebranch.bus_fr[k]
        kj = self.psd.ebranch.bus_to[k]
        return self.model.pf[k, s] == -self.psd.ebranch.b_lin[k]*(self.model.th[ki, s]-self.model.th[kj, s])
    
    def _sl_inj(self, b: int, s: int):
        if b in self.psd.bus.set_with_demand:
            return self.model.sl[b, s]
        return 0
    
    def _total_pg_cost(self) -> pyo.Expression:
        return sum([self.psd.sce.data[s, -1] * self.psd.gen.cost[g] * self.model.pg[g, s] \
                    for g in self.psd.gen.set_all for s in self.psd.sce.set_obs])
    
    def _total_sl_cost(self) -> pyo.Expression:
        return sum([self.psd.sce.data[s, -1] * self.psd.bus.sl_cost*self.model.sl[b, s] \
                    for b in self.psd.bus.set_with_demand for s in self.psd.sce.set_obs])
    
    def get_results(self, export: bool=True,
                    display: bool=True,
                    file_name: str="source/.results/results.txt",
                    name_file_test: str=None) -> None:
        with open(file_name, "w") as file:
            for idx, out in enumerate([sys.stdout, file]):
                if idx == 0 and not display:
                    continue
                if idx == 1 and not export:
                    continue
                print("-----------------------------------------", file=out)
                print("-----------------Results-----------------", file=out)
                print("-----------------------------------------", file=out)

                self._print_bus_data(out=out)
                self._print_ebranch_data(out=out)
                self._print_gen_data(out=out)
                
                print("\nObjective:", file=out)
                print(pyo.value(self.model.obj), file=out)

                print("\nTotal Power generation cost:", file=out)
                print(pyo.value(self._total_pg_cost()), file=out)

                print("\nTotal Load shedding cost:", file=out)
                print(pyo.value(self._total_sl_cost()), file=out)

        self._extract_pyo_values()
        if name_file_test is not None:
            np.save(name_file_test, self.results)
    
    def _print_bus_data(self, out) -> None:
        print("\n\n", file=out)
        ncol = 4
        print_centered_text("Bus data", file=out, ncol=ncol)
        for s in self.psd.sce.set_obs:
            print("\nScenario: {}".format(s), file=out)
            print(table_format(ncol=ncol).format("Bus", "pg", "LShed", "Angle"), file=out)
            for b in self.psd.bus.set_all:
                bus = int_format(b+1)
                gen = float_format(self._pg_inj(b, s))
                lshed = float_format(self._sl_inj(b, s))
                angle = float_format(self.model.th[b, s])
                print(bus + gen + lshed + angle, file=out)
    
    def _print_ebranch_data(self, out) -> None:
        print("\n\n", file=out)
        ncol = 5
        print_centered_text("Existent branch data", file=out, ncol=ncol)
        for s in self.psd.sce.set_obs:
            print("\nScenario: {}".format(s), file=out)
            print(table_format(ncol=ncol).format("Branch", "fr", "to", "pflow", "losses"), file=out)
            for k in self.psd.ebranch.set_all:
                branch = int_format(k+1)
                fr = int_format(self.psd.ebranch.bus_fr[k]+1)
                to = int_format(self.psd.ebranch.bus_to[k]+1)
                pflow = float_format(self.model.pf[k, s])
                losses = float_format(self.losses[k, s])
                print(branch + fr + to + pflow + losses, file=out)
    
    def _print_gen_data(self, out) -> None:
        print("\n\n", file=out)
        ncol = 4
        print_centered_text("Generation data", file=out, ncol=ncol)
        for s in self.psd.sce.set_obs:
            print("\nScenario: {}".format(s), file=out)
            print(table_format(ncol=ncol).format("Gen", "Bus", "pg", "cost"), file=out)
            for g in self.psd.gen.set_all:
                gen = int_format(g+1)
                bus = int_format(self.psd.gen.bus[g]+1)
                pg = float_format(self.model.pg[g, s])
                cost = float_format(self.model.pg[g, s]*self.psd.gen.cost[g])
                print(gen + bus + pg + cost, file=out)
    
    def _extract_pyo_values(self) -> None:
        self.results = dict()

        # Extracting results
        self.results["pg"] = pyo_extract_2D(self.model.pg, self.psd.gen.set_all, self.psd.sce.set_obs)
        self.results["th"] = pyo_extract_2D(self.model.th, self.psd.bus.set_all, self.psd.sce.set_obs)
        self.results["sl"] = pyo_extract_2D(self.model.sl, self.psd.bus.set_with_demand, self.psd.sce.set_obs)
        self.results["pf"] = pyo_extract_2D(self.model.pf, self.psd.ebranch.set_all, self.psd.sce.set_obs)

def main_opf_sce(data_file: str, sce_file: str, name_file_test: str=None):
    system_data = read_from_MATPOWER(data_file)
    psd = PowerSystemData(system_data=system_data, sce_file=sce_file)
    psd.bus.define_all_areas_as_zero()  # Considered historical series has only one area
    op = OPFSce(psd)
    op.define_model(debug=True)
    op.solve_model()
    op.get_results(name_file_test=name_file_test)
    return op.results

if __name__ == "__main__":
    data_file = "source/data/matpower/case3_sce.m"
    sce_file = "source/data/scenarios/load_test.csv"

    is_for_testing = False
    if is_for_testing:
        name_file_test = "source/tests/results/res_OPFBasic_sce_case3.npy"
        main_opf_sce(data_file=data_file, sce_file=sce_file, name_file_test=name_file_test)
    else:
        main_opf_sce(data_file=data_file, sce_file=sce_file)
        