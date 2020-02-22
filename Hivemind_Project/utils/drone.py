from math import inf

from rlbot.utils.structures.bot_input_struct import PlayerInput

class Drone:

    def __init__(self, index):
        self.index = index
        self.controls = PlayerInput()

        self.recovery = None
        self.half_flip = None
        self.aerial = None
        self.time_on_ground = inf
