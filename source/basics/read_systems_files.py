from dataclasses import dataclass
class ReadSystemsFiles():
    def __init__(self, data_file: str) -> None:
        self.data_file = data_file
        self.header_types = HeaderTypes()
        pass
    
    
    def read_from_anarede(self) -> None:
        ...

    
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