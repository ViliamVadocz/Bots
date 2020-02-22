from typing import Dict

from rlbot.agents.hivemind.python_hivemind import PythonHivemind
from rlbot.utils.structures.bot_input_struct import PlayerInput
from rlbot.utils.structures.game_data_struct import GameTickPacket

from rlutilities.linear_algebra import vec3, dot, norm, normalize
from rlutilities.mechanics import Wavedash
from rlutilities.simulation import Game

from utils.drone import Drone

from manoeuvres.recovery import Recovery
from manoeuvres.half_flip import HalfFlip
from manoeuvres.aerial import Aerial

class Overmind(PythonHivemind):

    def initialize_hive(self, packet: GameTickPacket) -> None:
        self.logger.info('The Swarm Awakens...')

        # Find out team by looking at packet.
        # drone_indices is a set, so you cannot just pick first element.
        my_index = next(iter(self.drone_indices))
        self.team = packet.game_cars[my_index].team

        # Create Drone objects for each drone.
        self.drones = [Drone(index) for index in self.drone_indices]

        # Create Game object.
        self.game = Game(my_index, self.team)
        self.field_info = self.get_field_info()
        self.update_game(packet)
        self.game.set_mode("soccar")

    def get_outputs(self, packet: GameTickPacket) -> Dict[int, PlayerInput]:

        self.update_game(packet)
        dt = self.game.time_delta

        # Reset controls.
        for drone in self.drones:
            drone.controls = PlayerInput()

        for drone in self.drones:
            car = self.game.cars[drone.index]

            # Handle time_on_ground
            if car.on_ground: 
                drone.time_on_ground += dt
            else:
                drone.time_on_ground = 0.0
            
            # Aerial!
            if drone.aerial is not None:
                drone.aerial.step(dt)
                drone.controls = to_player_input(drone.aerial.controls)
                
                if drone.aerial.finished:
                    drone.aerial = None

            else:
                # Recovery!
                if drone.time_on_ground < 0.2 :
                    if drone.recovery is None:
                        drone.recovery = Recovery(car)

                    drone.recovery.step(dt)
                    drone.controls = to_player_input(drone.recovery.controls)

                else:
                    # Reset after recovery.
                    if drone.recovery is not None:
                        drone.recovery = None

                    # Just go forward for a bit.
                    drone.controls.throttle = 1.0

                    # Initiate aerial.
                    if drone.aerial is None:
                        drone.aerial = Aerial(car, vec3(0, 0, 1000), self.game.time, 4.0)
    
            # # If going backwards, do a half-flip.
            # if drone.half_flip is None:
            #     speed = norm(car.velocity)
            #     if speed > 500 and dot(normalize(car.velocity), car.forward()) < -0.5:
            #         drone.half_flip = HalfFlip(car)

            #     drone.controls.throttle = -1.0

            # else:
            #     drone.half_flip.step(dt)
            #     drone.controls = to_player_input(drone.half_flip.controls)

            #     if drone.half_flip.finished:
            #         drone.half_flip = None

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

