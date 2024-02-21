from abc import abstractmethod, ABC
from powersystem import PowerSystemData
import pyomo.environ as pyo
import numpy as np
from funcs.funcs import print_pyovar, print_centered_text

class OptimizationProblem(ABC):
    
    @abstractmethod
    def define_model(self):
        ...

    @abstractmethod
    def solve_model(self):
        ...

    @abstractmethod
    def get_results(self):
        ...

class OPFBasic(OptimizationProblem):

    def __init__(self, psd: PowerSystemData) -> None:
        # PowerSystemData injection
        self.psd = psd
    
    def define_model(self, debug: bool = False):
        # Model
        self.model = pyo.ConcreteModel(name=self.__class__.__name__)

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
    
    def get_results(self, export=True, display=True) -> None:
        if export:
            self._export_results()
        if display:
            self._display_results()
    
    def _bounds_pf(self, _, k: int) -> tuple:
        return (-self.psd.ebranch.flow_max[k], +self.psd.ebranch.flow_max[k])
    
    def _bounds_pg(self, _, g: int) -> tuple:
        return (0, self.psd.gen.pg_max[g])
    
    def _bounds_sl(self, _, b: int) -> tuple:
        return (0, self.psd.bus.pd_max[b])
    
    def _create_objective(self) -> pyo.Expression:
        return self._total_pg_cost()+self._total_sl_cost()
    
    def _pf_inj(self, b) -> pyo.Expression:
        pf_inj = 0
        for k in np.where(self.psd.ebranch.bus_fr == b)[0]:
            pf_inj += self.model.pf[k]
        for k in np.where(self.psd.ebranch.bus_to == b)[0]:
            pf_inj -= self.model.pf[k]
        return pf_inj
    
    def _pg_inj(self, b) -> pyo.Expression:
        pg_inj = 0
        for g in np.where(self.psd.gen.bus == b)[0]:
            pg_inj += self.model.pg[g]
        return pg_inj
    
    def _rule_power_balance(self, _, b) -> pyo.Expression:
        return self._pg_inj(b)-self._pf_inj(b)+self._sl_inj(b) == self.psd.bus.pd_max[b]
    
    def _rule_power_flow(self, _, k) -> pyo.Expression:
        i = self.psd.ebranch.bus_fr[k]
        j = self.psd.ebranch.bus_to[k]
        return self.model.pf[k] == self.psd.ebranch.b[k]*(self.model.th[i]-self.model.th[j])
    
    def _sl_inj(self, b):
        if b in self.psd.bus.set_with_demand:
            return self.model.sl[b]
        return 0
    
    def _total_pg_cost(self) -> pyo.Expression:
        return sum([self.psd.gen.cost[g]*self.model.pg[g] for g in self.psd.gen.set_all])
    
    def _total_sl_cost(self) -> pyo.Expression:
        return sum([self.psd.bus.sl_cost*self.model.sl[b] for b in self.psd.bus.set_with_demand])
    
    def _display_results(self) -> None:
        print("\n\n-------Results-------\n\n")

        print_pyovar(title="Active Power Generation:", 
                    var=self.model.pg,
                    set=self.psd.gen.set_all)
        
        print_pyovar(title="Load Shedding:", 
                    var=self.model.sl,
                    set=self.psd.bus.set_with_demand)
        
        print_pyovar(title="Active Power Flow:", 
                    var=self.model.pf,
                    set=self.psd.ebranch.set_all)
        
        print_pyovar(title="Angles:", 
                    var=self.model.th,
                    set=self.psd.bus.set_all)

        print("\nObjective:")
        print(pyo.value(self.model.obj))

        print("\nTotal Power generation cost")
        print(pyo.value(self._total_pg_cost()))

        print("\nTotal Load shedding cost")
        print(pyo.value(self._total_sl_cost()))
    
    def _export_results(self) -> None:
        with open("results.txt", "w") as file:
            print_centered_text("Bus data", file=file, total_length=6+3*9)
            print("{:>6}{:>9}{:>9}{:>9}".format("Bus", "Gen", "LShed", "Angle"), file=file)
            for b in self.psd.bus.set_all:
                bus = self._int_format(b+1)
                gen = self._float_format(self._pg_inj(b))
                lshed = self._float_format(self._sl_inj(b))
                angle = self._float_format(self.model.th[b])
                print(bus + gen + lshed + angle, file=file)
            
            print("\n\n", file=file)
            print_centered_text("Existent branch data", file=file, total_length=3*6+9)
            print("{:>6}{:>6}{:>6}{:>9}".format("Branch", "fr", "to", "pflow"), file=file)
            for k in self.psd.ebranch.set_all:
                branch = self._int_format(k+1)
                fr = self._int_format(self.psd.ebranch.bus_fr[k]+1)
                to = self._int_format(self.psd.ebranch.bus_to[k]+1)
                pflow = self._float_format(self.model.pf[k])
                print(branch + fr + to + pflow, file=file)

    def _float_format(self, number: float) -> None:
        return "{:>9.4f}".format(pyo.value(number))

    def _int_format(self, number: int) -> None:
        return "{:>6}".format(number)
