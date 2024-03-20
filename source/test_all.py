import unittest
import numpy as np
from opf_basic import main_opf_basic
from opf_basic_losses import main_opf_basic_losses
from opf_sce import main_opf_sce
from tep_basic import main_tep_basic
from opf_monte_carlo import main_opf_monte_carlo


class TestAll(unittest.TestCase):
    def test_OPFBasic(self):
        data_file = "source/tests/data/MATPOWER/case3_Basics.m"
        results = np.load("source/tests/results/res_OPFBasic_case3.npy",allow_pickle=True).tolist()
        numpy_assert_almost_dict_values(main_opf_basic(data_file=data_file), results)

    
    def test_OPFBasicLoss(self):
        data_file = "source/tests/data/MATPOWER/case3_Basics.m"
        results = np.load("source/tests/results/res_OPFBasic_loss_case3.npy",allow_pickle=True).tolist()
        numpy_assert_almost_dict_values(main_opf_basic_losses(data_file=data_file), results)

    
    def test_OPFSce(self):
        data_file = "source/tests/data/MATPOWER/case3_sce.m"
        results = np.load("source/tests/results/res_OPFBasic_sce_case3.npy",allow_pickle=True).tolist()
        sce_file = "source/tests/data/scenarios/load_test.csv"
        numpy_assert_almost_dict_values(main_opf_sce(data_file=data_file, sce_file=sce_file), results)

    
    def test_TEPBasic(self):
        data_file = "source/tests/data/MATPOWER/case3_Basics.m"
        results = np.load("source/tests/results/res_TEPBasic_case3.npy",allow_pickle=True).tolist()
        numpy_assert_almost_dict_values(main_tep_basic(data_file=data_file), results)

    # @unittest.skip("Under implementation")
    def test_OPFMonteCarlo(self):
        data_file = "source/tests/data/MATPOWER/case24_ieee_rts_reliability.m"
        results = np.load("source/tests/results/res_OPFMonteCarlo_case24_ieee_rts_reliability.npy",allow_pickle=True).tolist()
        numpy_assert_almost_dict_values(main_opf_monte_carlo(data_file=data_file), results)

        
def dic_to_keys_values(dic):
    keys, values = list(dic.keys()), list(dic.values())
    return keys, values

def numpy_assert_almost_dict_values(dict1, dict2):
    keys1, values1 = dic_to_keys_values(dict1)
    keys2, values2 = dic_to_keys_values(dict2)
    np.testing.assert_equal(keys1, keys2)
    for idx, _ in enumerate(values1):
        np.testing.assert_almost_equal(values1[idx], values2[idx])

if __name__ == "__main__":
    unittest.main(exit=False)