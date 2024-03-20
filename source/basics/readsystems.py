import re
import numpy as np


def read_from_MATPOWER(data_file: str) -> dict:
    matrices = {}  # Dictionary to store the matrices

    with open(data_file, 'r') as file:
        content = file.read()

        # Find all parts within line comments
        parts = re.findall(r'%%\s+(.*?)\n(?:(?!%%).)*?mpc\.(\w+)\s*=\s*\[\s*(.*?)(?=\n\s*];)', content, re.DOTALL)

        for _, matrix_name, matrix_content in parts:
            # Remove comments from the part
            matrix_content_no_comments = re.sub(r'%.*', '', matrix_content)
            
            # Split the lines of the matrix based on the ";"
            matrix_lines = matrix_content_no_comments.split(';')
            
            # Remove leading and trailing whitespaces from each line
            matrix_lines = [line.strip() for line in matrix_lines if line.strip()]
            
            # Split the numbers into lists to form the matrix rows
            matrix = [line.split() for line in matrix_lines]

            # Convert the numbers to floats
            matrix = [[float(num) for num in line] for line in matrix]

            # Store the matrix in the dictionary
            matrices[matrix_name] = np.array(matrix)

    return matrices

def read_from_ANAREDE(data_file: str) -> dict:
    sections = {}
    with open(data_file, 'r') as file:
        lines = file.readlines()
        current_section = None
        current_lines = []
        for line in lines:
            header = line.strip()
            if not header.startswith("("):  # Se não começar com "("
                if current_section is not None:
                    line = read_section(line)
                current_section = header
                current_lines = []
            else:
                current_lines.append(line)
        if current_section is not None and current_lines:
            sections[current_section] = read_section(current_lines)
    return sections



def read_section(lines):
    if not lines:
        return None
    data = []
    for line in lines:
        if line.strip() == "99999":
            break
        values = line.split()
        data.append([float(value) if "." in value else int(value) for value in values])
    return np.array(data)