import numpy as np
import pyomo.environ as pyo

def print_pyovar(title: str, var: pyo.Var, set: np.ndarray) -> None:
    print(title)
    for idx in set:
        print(var[idx], pyo.value(var[idx]), sep=' = ')
    print()

def print_centered_text(text, file, total_length, fill_char='-'):
    space = total_length-len(text)
    if space <= 0:
        return text
    fill_left = space//2
    fill_right = space-fill_left
    print(fill_char*fill_left + text + fill_char*fill_right, file=file)