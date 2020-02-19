from rlutilities.simulation import Car, Input

class Manoeuvre:

    def __init__(self, car: Car):
        self.car: Car = car
        self.controls = Input()
        self.finished = False

    def step(self, dt: float):
        raise NotImplementedError