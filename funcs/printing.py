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
