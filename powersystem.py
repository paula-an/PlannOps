import numpy as np

class PowerSystemData:
    """Class to construct Power System Raw Data"""
    def __init__(self,
                 system_data: np.ndarray,
                 power_base: float = 100) -> None:
        self.power_base = power_base
        self.bus = BusData(system_data, power_base)
        self.ebranch = ExistentBranchData(system_data, power_base)
        self.gen = GeneratorsData(system_data, power_base)

        # Load Sheding cost
        self.bus.sl_cost = 100*max(self.gen.cost)


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
    
    def set_new(self):
        raise NotImplementedError()
    
    def delete(self):
        raise NotImplementedError()


class ExistentBranchData:
    """Class to load existent branch data"""
    def __init__(self,
                 system_data: np.ndarray,
                 power_base: float) -> None:
        self.bus_fr = system_data["branch"][:, 0].astype(int)-1  # From bus number
        self.bus_to = system_data["branch"][:, 1].astype(int)-1  # To bus number
        self.r = system_data["branch"][:, 2]  # Series resistance
        self.x = system_data["branch"][:, 3]  # Series reactance
        self.b_shunt = 0.5*system_data["branch"][:, 4]  # Susceptance shunt
        
        # Calculating series condutance and susceptance
        deno = self.r**2+self.x**2
        self.g = +self.r/deno
        self.b = -self.x/deno

        # Max apparent power flow
        self.flow_max_MW = system_data["branch"][:, 5]
        self.unlimited_branches = np.where(self.flow_max_MW==0)[0]
        self.flow_max_MW[self.unlimited_branches] = 99999
        self.flow_max = self.flow_max_MW/power_base

        # Transformers TAPs
        self.tap = system_data["branch"][:, 8]
        self.tap[np.where(self.tap == 0)] = 1

        # Misc
        self.len = len(self.bus_fr)
        self.set_all = np.arange(self.len)
    
    def set_new(self):
        raise NotImplementedError()
    
    def delete(self):
        raise NotImplementedError()


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