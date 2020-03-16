from math import inf

from rlbot.utils.structures.bot_input_struct import PlayerInput

class Drone:

    def __init__(self, index):
        self.index = index
        self.controls = PlayerInput()

        self.time_on_ground = inf
        self.time_off_ground = 0.0
        
        self.ready = False
