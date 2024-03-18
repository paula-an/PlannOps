import numpy as np

class PowerSystemData:
    """Class to construct Power System Raw Data"""
    def __init__(self,
                 system_data: np.ndarray,
                 power_base: float = 100,
                 max_ang_opening: float = 4*np.pi,
                 sce_file: str = None) -> None:
        
        self.power_base = power_base
        self.max_ang_opening = max_ang_opening

        self.bus = BusData(system_data, power_base)

        self.ebranch = BranchData(system_data=system_data,
                                  data_key="branch",
                                  power_base=power_base,
                                  max_ang_opening=max_ang_opening)
        if "xbranch" in system_data:
            self.xbranch = BranchData(system_data=system_data,
                                  data_key="xbranch",
                                  power_base=power_base,
                                  max_ang_opening=max_ang_opening)
            self.xbranch_bin = XBranchBin(self.xbranch)

        self.gen = GeneratorsData(system_data, power_base)

        # Load Sheding cost
        self.bus.sl_cost = 100*max(self.gen.cost)

        # Scenario
        if sce_file is not None:
            self.sce = ScenariosData(sce_file)

        # Isolated buses treatment
        self.find_isolated_buses()
        if np.any(self.bus.is_isolated):
            if "xbranch" not in system_data:
                raise UserWarning("Buses {} are impossible to be connected!!!".format(np.where(self.bus.is_isolated)[0]))
            self.create_dumb_grid()
            self.find_isolated_buses()
            if np.any(self.bus.is_isolated):
                raise UserWarning("Buses {} are impossible to be connected!!!".format(np.where(self.bus.is_isolated)[0]))
        
    def find_isolated_buses(self) -> None:
        for b in np.where(self.bus.is_isolated)[0]:
            for k in self.ebranch.set_all:
                if b in {self.ebranch.bus_fr[k], self.ebranch.bus_to[k]}:
                    self.bus.is_isolated[b] = False
                    break
    
    def create_dumb_grid(self) -> None:
        for b in np.where(self.bus.is_isolated)[0]:
            for k in self.xbranch.set_all:
                if b in {self.xbranch.bus_fr[k], self.xbranch.bus_to[k]}:
                    self.create_dumb_line(self.xbranch.bus_fr[k], self.xbranch.bus_to[k])
                    
    
    def create_dumb_line(self, bus_fr: int, bus_to: int) -> None:
        self.ebranch.is_dumb = np.append(self.ebranch.is_dumb, True)
        self.ebranch.bus_fr = np.append(self.ebranch.bus_fr, bus_fr)
        self.ebranch.bus_to = np.append(self.ebranch.bus_to, bus_to)
        self.ebranch.r = np.append(self.ebranch.r, 0)
        self.ebranch.x = np.append(self.ebranch.x, 1/self.ebranch.b_dumb)
        self.ebranch.b_shunt = np.append(self.ebranch.b_shunt, 0)
        self.ebranch.g = np.append(self.ebranch.g, 0)
        self.ebranch.b = np.append(self.ebranch.b, self.ebranch.b_dumb)
        self.ebranch.b_lin = np.append(self.ebranch.b_lin, self.ebranch.b_dumb)
        self.ebranch.unlimited_branches = np.append(self.ebranch.unlimited_branches, False)
        self.ebranch.flow_max_MW = np.append(self.ebranch.flow_max_MW, 0)
        self.ebranch.flow_max = np.append(self.ebranch.flow_max, self.ebranch.flow_max_dumb)
        self.ebranch.tap = np.append(self.ebranch.tap, 1)
        self.ebranch.bigM = np.append(self.ebranch.bigM, self.ebranch.bigM_dumb)
        self.ebranch.set_all = np.append(self.ebranch.set_all, self.ebranch.len)
        self.ebranch.len += 1

class BusData:
    """Class to load bus data"""
    def __init__(self,
                 system_data: np.ndarray,
                 power_base: float) -> None:
        self.type = system_data["bus"][:, 1].astype(int)  # Bus type
        self.pd_max_MW = system_data["bus"][:, 2]  # Max active power demand (MW)
        self.pd_max = self.pd_max_MW/power_base  # Max active power demand (pu)
        self.qd_max_MW = system_data["bus"][:, 3]  # Max reactive power demand (MW)
        self.qinj_MW = system_data["bus"][:,5]  # Reactive power injection (MW)
        self.qd_max = (self.qd_max_MW-self.qinj_MW)/power_base  # Max reactive power demand (pu)
        self.area = system_data["bus"][:, 8].astype(int)  # Bus area
        
        # Misc
        self.len = len(self.type)
        self.set_all = np.arange(self.len)
        self.set_with_demand = np.where(self.pd_max > 0)[0]
        self.len_with_demand = len(self.set_with_demand)

        # Initializing isolated buses
        self.is_isolated = np.ones(self.len, dtype=bool)
    
    def new(self):
        raise NotImplementedError()
    
    def delete(self):
        raise NotImplementedError()
    
    def define_all_as_demand(self):
        self.set_with_demand = np.copy(self.set_all)

    def define_all_areas_as_zero(self):
        self.area = np.zeros_like(self.area)

class BranchData:
    """Class to load existent branch data"""
    def __init__(self,
                 system_data: np.ndarray,
                 data_key: str,
                 power_base: float,
                 max_ang_opening: float) -> None:
        self.bus_fr = system_data[data_key][:, 0].astype(int)-1  # From bus number
        self.bus_to = system_data[data_key][:, 1].astype(int)-1  # To bus number

        # Misc
        self.len = len(self.bus_fr)
        self.set_all = np.arange(self.len)

        self._remove_repeated_lines()

        self.r = system_data[data_key][:, 2][self.unique_lines] / self.nlines  # Series resistance
        self.x = system_data[data_key][:, 3][self.unique_lines] / self.nlines  # Series reactance
        self.b_shunt = 0.5*system_data[data_key][:, 4][self.unique_lines] * self.nlines  # Susceptance shunt
        
        # Calculating series condutance and susceptance
        deno = self.r**2+self.x**2
        self.g = +self.r/deno
        self.b = -self.x/deno
        self.b_lin = -1/self.x

        # Max apparent power flow
        self.flow_max_MW = system_data[data_key][:, 5][self.unique_lines] * self.nlines
        self.unlimited_branches = np.zeros(self.len, dtype=bool)
        self.unlimited_branches[np.where(self.flow_max_MW==0)[0]] = True
        self.flow_max_MW[self.unlimited_branches] = 99999
        self.flow_max = self.flow_max_MW/power_base

        # Transformers TAPs
        self.tap = system_data[data_key][:, 8][self.unique_lines]
        self.tap[np.where(self.tap == 0)] = 1

        # Big M
        self.bigM = -max_ang_opening * self.b_lin

        # Dumb lines
        min_flow_max = min(self.flow_max)/100
        self.b_dumb = -min_flow_max/max_ang_opening
        self.flow_max_dumb = 1.1*min_flow_max
        self.is_dumb = np.zeros(self.len, dtype=bool)
        self.bigM_dumb = self.flow_max_dumb

        # Maximum number of expansion lines
        if data_key != "xbranch":
            return
        
        if np.shape(system_data[data_key])[1] == 15:
            self.invT_max = system_data[data_key][:, 13][self.unique_lines].astype(int)
            self.invT_cost = system_data[data_key][:, 14][self.unique_lines]
        else:
            self.invT_max = 3*np.ones(self.len)
            self.invT_cost = 1e6
        
        del self.unique_lines
    
    def new(self):
        raise NotImplementedError()
    
    def delete(self):
        raise NotImplementedError()
    
    def down(self, k: int):
        raise NotImplementedError()
    
    def up(self, k: int):
        raise NotImplementedError()
    
    def _remove_repeated_lines(self) -> None:
        # Finding unique lines
        self.unique_lines = np.ones(self.len, dtype=bool)
        self.nlines = np.ones(self.len, dtype=int)
        for k1 in range(self.len):
            fr1 = self.bus_fr[k1]
            to1 = self.bus_to[k1]
            if not self.unique_lines[k1]:
                continue
            for k2 in range(k1+1, self.len):
                if self.bus_fr[k2] == fr1 and self.bus_to[k2] == to1:
                    self.unique_lines[k2] = False
                    self.nlines[k1] += 1
        
        if np.all(self.unique_lines):
            return
        
        # Update attributes
        self.bus_fr = self.bus_fr[self.unique_lines]
        self.bus_to = self.bus_to[self.unique_lines]
        self.nlines = self.nlines[self.unique_lines]

        # Update misc
        self.len = len(self.bus_fr)
        self.set_all = np.arange(self.len)

    
class XBranchBin:
    def __init__(self, xbranch: BranchData) -> None:
        
        # Misc
        self.len = sum(xbranch.invT_max)
        self.set_all = np.arange(self.len)

        # Data for binary models
        self.bus_fr = np.zeros(self.len, dtype=int)  # From bus number
        self.bus_to = np.zeros(self.len, dtype=int)  # To bus number

        self.r = np.zeros(self.len, dtype=float)
        self.x = np.zeros(self.len, dtype=float)
        self.b_shunt = np.zeros(self.len, dtype=float)
        self.g = np.zeros(self.len, dtype=float)
        self.b = np.zeros(self.len, dtype=float)
        self.b_lin = np.zeros(self.len, dtype=float)
        self.flow_max = np.zeros(self.len, dtype=float)
        self.tap = np.zeros(self.len, dtype=float)
        self.bigM = np.zeros(self.len, dtype=float)
        self.invT_cost = np.zeros(self.len, dtype=float)

        idx = 0
        for k in xbranch.set_all:
            for _ in range(xbranch.invT_max[k]):
                self.bus_fr[idx] = xbranch.bus_fr[k]  # From bus number
                self.bus_to[idx] = xbranch.bus_to[k]  # To bus number
                self.r[idx] = xbranch.r[k]
                self.x[idx] = xbranch.x[k]
                self.b_shunt[idx] = xbranch.b_shunt[k]
                self.g[idx] = xbranch.g[k]
                self.b[idx] = xbranch.b[k]
                self.b_lin[idx] = xbranch.b_lin[k]
                self.flow_max[idx] = xbranch.flow_max[k]
                self.tap[idx] = xbranch.tap[k]
                self.bigM[idx] = xbranch.bigM[k]
                self.invT_cost[idx] = xbranch.invT_cost[k]

                idx += 1


class GeneratorsData:
    """Class to load generators data"""
    def __init__(self,
                 system_data: np.ndarray,
                 power_base: float) -> None:
        self.bus = system_data["gen"][:, 0].astype(int)-1
        self.pg_MW = system_data["gen"][:, 1]
        self.pg = self.pg_MW/power_base
        self.qg_MW = system_data["gen"][:, 2]
        self.qg = self.qg_MW/power_base
        self.qg_max_MW = system_data["gen"][:, 3]
        self.qg_max = self.qg_max_MW/power_base
        self.qg_min_MW = system_data["gen"][:, 4]
        self.qg_min = self.qg_min_MW/power_base
        self.pg_max_MW = system_data["gen"][:, 8]
        self.pg_max = self.pg_max_MW/power_base
        self.pg_min_MW = system_data["gen"][:, 9]
        self.pg_min = self.pg_min_MW/power_base
        self.type = system_data["gen"][:, 21].astype(int)

        # Misc
        self.len = len(self.bus)
        self.set_all = np.arange(self.len)

        # Generation cost
        self.cost = np.zeros(self.len)
        co2tax = system_data["c02tax"][0, 0]
        for gen_idx in self.set_all:
            cost_idx = self.type[gen_idx]-1
            opecost = system_data["gencost"][cost_idx, 2]
            co2prod = system_data["gencost"][cost_idx, 3]
            self.cost[gen_idx] = opecost + co2prod*co2tax
    
    def set_new(self):
        raise NotImplementedError()
    
    def delete(self):
        raise NotImplementedError()
    
class ScenariosData:
    def __init__(self, file) -> None:
        self.data = np.genfromtxt(file, delimiter=",")

        # Misc
        (self.len_obs, self.len_series) = np.shape(self.data)
        self.set_obs = np.arange(self.len_obs)
        self.set_series = np.arange(self.len_series)