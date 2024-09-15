from dataclasses import dataclass
import re
import numpy as np

def ReadSystemsFiles(data_file: str) -> None:
    file_extension = data_file.split(".")[-1].lower()
    match file_extension:
        case "m":
            return read_from_MATPOWER(data_file=data_file)
        case "pwf":
            # read_from_ANAREDE()
            raise NotImplementedError()
        case _:
            raise UserWarning("File Extension not supported")
    
    # self.header_types = HeaderTypes()
    # pass
    
    
def read_from_ANAREDE(data_file: str) -> dict:
    # https://github.com/LAMPSPUC/PWF.jl
    sections = {}
    with open(self.data_file, 'r') as file:
        lines = file.readlines()
        current_section = None
        current_lines = []
        for line in lines:
            header = line.strip()
            if not header.startswith("("):  # Se não começar com "("
                if current_section is not None:
                    line = self.read_section(line)
                current_section = header
                current_lines = []
            else:
                current_lines.append(line)
        if current_section is not None and current_lines:
            sections[current_section] = read_section(current_lines)
    return sections



def read_section(self, lines):
    if not lines:
        return None
    data = []
    for line in lines:
        if line.strip() == "99999":
            break
        values = line.split()
        data.append([float(value) if "." in value else int(value) for value in values])
    return np.array(data)

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

    
@dataclass
class HeaderTypes():
    dbar_types = [
            ("NUMBER", int, slice(0, 5)), 
            ("OPERATION", str, slice(5, 6)), 
            ("STATUS", str, slice(6, 7)), 
            ("TYPE", int, slice(7, 8)), 
            ("BASE VOLTAGE GROUP", str, slice(8, 10)),
            ("NAME", str, slice(10, 22)), 
            ("VOLTAGE LIMIT GROUP", str, slice(22, 24)),
            ("VOLTAGE", float, slice(24, 28)), 
            ("ANGLE", float, slice(28, 32)),
            ("ACTIVE GENERATION", float, slice(32, 37)), 
            ("REACTIVE GENERATION", float, slice(37, 42)),
            ("MINIMUM REACTIVE GENERATION", float, slice(42, 47)),
            ("MAXIMUM REACTIVE GENERATION", float, slice(47, 52)), 
            ("CONTROLLED BUS", int, slice(52, 58)),
            ("ACTIVE CHARGE", float, slice(58, 63)), 
            ("REACTIVE CHARGE", float, slice(63, 68)),
            ("TOTAL REACTIVE POWER", float, slice(68, 73)), 
            ("AREA", int, slice(73, 76)),
            ("CHARGE DEFINITION VOLTAGE", float, slice(76, 80)), 
            ("VISUALIZATION", int, slice(80, 81)),
            ("AGGREGATOR 1", int, slice(81, 84)), 
            ("AGGREGATOR 2", int, slice(84, 87)),
            ("AGGREGATOR 3", int, slice(87, 90)), 
            ("AGGREGATOR 4", int, slice(90, 93)),
            ("AGGREGATOR 5", int, slice(93, 96)), 
            ("AGGREGATOR 6", int, slice(96, 99)),
            ("AGGREGATOR 7", int, slice(99, 102)), 
            ("AGGREGATOR 8", int, slice(102, 105)),
            ("AGGREGATOR 9", int, slice(105, 108)), 
            ("AGGREGATOR 10", int, slice(108, 111))
            ]
    
    dlin_types = [
        ("De", int, slice(0, 4)), 
        ("d", str, slice(4, 5)), 
        ("O", int, slice(5, 8)), 
        ("d_Pa", float, slice(8, 13)), 
        ("NcEP", float, slice(13, 16)), 
        ("R", str, slice(16, 20)), 
        ("X", str, slice(20, 24)), 
        ("Mvar", float, slice(24, 30)), 
        ("Tap", float, slice(30, 36)), 
        ("Tmn", float, slice(36, 42)), 
        ("Tmx", float, slice(42, 48)), 
        ("Phs", str, slice(48, 51)), 
        ("Bc", str, slice(51, 56)), 
        ("Cn", str, slice(56, 58)), 
        ("Ce", str, slice(58, 61)), 
        ("Ns", int, slice(61, 65))
    ]