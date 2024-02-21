from readsystems import read_from_MATPOWER
from powersystem import PowerSystemData
from problems import opt

def main():
    file_name = "dataMATPOWER/case3.m"
    system_data = read_from_MATPOWER(file_name)
    psd = PowerSystemData(system_data=system_data)
    opt_problem = opt.OPFBasic(psd)
    opt_problem.define_model(debug=True)
    opt_problem.solve_model()
    opt_problem.get_results()

if __name__ == "__main__":
    main()