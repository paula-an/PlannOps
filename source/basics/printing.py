import numpy as np
import pyomo.environ as pyo
import typing

def print_pyovar(title: str, var: pyo.Var, set: np.ndarray) -> None:
    print(title)
    for idx in set:
        print(var[idx], pyo.value(var[idx]), sep=' = ')
    print()

def print_centered_text(text: str, file: str, ncol:int, fill_char: str ='-') -> None:
    total_length = ncol*9
    space = total_length-len(text)
    if space <= 0:
        return text
    fill_left = space//2
    fill_right = space-fill_left
    print(fill_char*fill_left + text + fill_char*fill_right, file=file)

def float_format(number: float) -> str:
    return "{:>9.4f}".format(pyo.value(number))

def int_format(number: int) -> str:
    return "{:>9}".format(number)

def table_format(ncol: int) -> str:
    return ncol*"{:>9}"

def pyo_extract(var: pyo.Var, set: np.ndarray) -> np.ndarray:
    array = np.zeros(len(set))
    for arr_idx, set_idx in enumerate(set):
        array[arr_idx] = pyo.value(var[set_idx])
    return array

def pyo_extract_2D(var: pyo.Var, set_1D: np.ndarray, set_2D: np.ndarray) -> np.ndarray:
    array = np.zeros((len(set_1D), len(set_2D)))
    for arr_idx_1D, set_idx_1D in enumerate(set_1D):
        for arr_idx_2D, set_idx_2D in enumerate(set_2D):
            array[arr_idx_1D, arr_idx_2D] = pyo.value(var[set_idx_1D, set_idx_2D])
    return array
