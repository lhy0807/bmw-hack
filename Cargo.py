import pandas as pd

class Cargo:
    def __init__(self, size, vin, eta, code, plant, dda) -> None:
        self.size = size
        self.vin = vin
        self.eta = eta
        self.code = code
        self.plant = plant
        self.dda = dda