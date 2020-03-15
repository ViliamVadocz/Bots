from typing import Dict
from enum import Enum

from rlbot.agents.hivemind.python_hivemind import PythonHivemind
from rlbot.utils.structures.bot_input_struct import PlayerInput
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction

from rlutilities.linear_algebra import vec3, dot, norm, normalize
from rlutilities.mechanics import Drive
from rlutilities.simulation import Game

from util.drone import Drone
from util.general import team_sign
from util.goal_detector import find_future_goal

from manoeuvres.recovery import Recovery
from manoeuvres.half_flip import HalfFlip
from manoeuvres.aerial import Aerial
from manoeuvres.slow_to_pos import SlowToPos

class Overmind(PythonHivemind):

    def initialize_hive(self, packet: GameTickPacket) -> None:
        self.logger.info('The Swarm Awakens...')

        # Find out team by looking at packet.
        # drone_indices is a set, so you cannot just pick first element.
        my_index = next(iter(self.drone_indices))
        self.team = packet.game_cars[my_index].team
        self.sign = team_sign(self.team)
        self.phase = Phase.RESET

        # Create Drone objects for each drone.
        self.drones = [Drone(index) for index in self.drone_indices]
        assert len(self.drones) == 3, "The Swarm was hardcoded for exactly three drones."

        # Create Game object.
        self.game = Game(my_index, self.team)
        self.field_info = self.get_field_info()
        self.update_game(packet)
        self.game.set_mode("soccar")

        # Initialise all mechanics.
        for drone in self.drones:
            car = self.game.cars[drone.index]
            drone.recovery = Recovery(car)
            drone.half_flip = HalfFlip(car)
            drone.aerial = Aerial(car, vec3(0,0,0), 0, 0)
            drone.drive = Drive(car)
            drone.slow_to_pos = SlowToPos(car, vec3(0,0,0))
            drone.car = car

    def get_outputs(self, packet: GameTickPacket) -> Dict[int, PlayerInput]:

        self.update_game(packet)
        dt = self.game.time_delta

        # Ball prediction.
        ball_prediction: BallPrediction = self.get_ball_prediction_struct()
        future_goal = find_future_goal(ball_prediction)
        needs_saving = False
        if future_goal is not None:
            if future_goal.team == self.team:
                needs_saving = True

        # Reset controls.
        for drone in self.drones:
            drone.controls = PlayerInput()        
        
        # Drive to position.
        if self.phase == Phase.RESET:
            self.drones.sort(key=lambda drone: drone.car.position[0])
            self.right = self.drones[0]
            self.middle = self.drones[1]
            self.left = self.drones[2]
            
            self.right.slow_to_pos.target = self.sign * vec3(-900, -4900, 0)
            self.middle.slow_to_pos.target = self.sign * vec3(0, -5300, 0)
            self.left.slow_to_pos.target = self.sign * vec3(900, -4900, 0)

            finished = True
            for drone in self.drones:
                drone.slow_to_pos.step(dt)
                drone.controls = to_player_input(drone.slow_to_pos.controls)
                if not drone.slow_to_pos.finished:
                    finished = False

            # if finished:
            #     self.phase = Phase.ORIENT

        # Face correct directions.
        elif self.phase == Phase.ORIENT:
            pass

                

        # if car.boost < 20:
        #     if drone.drive is None:
        #         drone.drive = Drive(car)
        #         drone.drive.target = 
        #         drone.drive.step(dt)
        #         drone.controls = to_player_input(drone.drive.controls)

        return self.make_drone_controls_dict()

    def update_game(self, packet):
        self.game.read_game_information(
            packet,
            self.field_info
        )

    def make_drone_controls_dict(self) -> Dict[int, PlayerInput]:
        return {drone.index: drone.controls for drone in self.drones}


def to_player_input(controls) -> PlayerInput:
    """Convert controls to PlayerInput"""
    player_input = PlayerInput()
    player_input.throttle = controls.throttle
    player_input.steer = controls.steer
    player_input.pitch = controls.pitch
    player_input.yaw = controls.yaw
    player_input.roll = controls.roll
    player_input.jump = controls.jump
    player_input.boost = controls.boost
    player_input.handbrake = controls.handbrake
    # RLUtilities Input does not have a use_item attribute.
    if hasattr(controls, "use_item"):
        player_input.use_item = controls.use_item

    return player_input


class Phase(Enum):
    RESET = 0
    ORIENT = 1
    SAVE = 2
