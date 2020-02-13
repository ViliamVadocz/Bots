from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator

import numpy as np
from utils import Car, a3l, a3r, a3v, orient_matrix


class DataCollectionBot(BaseAgent):

    def initialize_agent(self):
        self.car = Car(self.index, self.team, self.name)
        self.last_time = 0.0

    def process(self, packet: GameTickPacket):
        # Processing game info.
        self.game_time = packet.game_info.seconds_elapsed
        self.dt = self.game_time - self.last_time
        self.last_time = self.game_time

        # From packet:
        self.car.pos = a3v(packet.game_cars[self.index].physics.location)
        self.car.rot = a3r(packet.game_cars[self.index].physics.rotation)
        self.car.vel = a3v(packet.game_cars[self.index].physics.velocity)
        self.car.ang_vel = a3v(packet.game_cars[self.index].physics.angular_velocity)
        # Calculated:
        self.car.orient_m = orient_matrix(self.car.rot)

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        return SimpleControllerState()
