from rlutilities.linear_algebra import vec2, dot
from rlutilities.mechanics import Dodge
from rlutilities.simulation import Car

from manoeuvres.manoeuvre import Manoeuvre

DODGE_DURATION = 0.12
STALL_START = 0.5
STALL_END = 0.7
BOOST_DELAY = 0.4
TIMEOUT = 2.0

class HalfFlip(Manoeuvre):

    def __init__(self, car: Car, use_boost=False):
        super().__init__(car)

        self.use_boost = use_boost
        self.dodge = Dodge(car)
        self.dodge.duration = DODGE_DURATION
        self.dodge.direction = vec2(-1 * car.forward())

        self.timer = 0.0

    def step(self, dt:float):

        self.dodge.step(dt)
        self.controls = self.dodge.controls

        if STALL_START < self.timer < STALL_END:
            self.controls.roll = 0.0
            self.controls.pitch = -1.0
            self.controls.yaw = 0.0

        if self.timer > STALL_END:
            self.controls.roll = 0.95
            self.controls.pitch = -1.0
            self.controls.yaw = 0.95

        if self.use_boost and self.timer > BOOST_DELAY:
            self.controls.boost = True
        else:
            self.controls.boost = False

        self.timer += dt

        self.finished = (self.timer > TIMEOUT) or \
                        (self.car.on_ground and self.timer > 0.5)
