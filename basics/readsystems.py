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