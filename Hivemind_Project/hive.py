from typing import Dict

from rlbot.utils.structures.bot_input_struct import PlayerInput
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.agents.hivemind.python_hivemind import PythonHivemind

from rlutilities.simulation import Game
from rlutilities.mechanics import Wavedash

from utils.drone import Drone

from manoeuvres.recovery import Recovery

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

        # Reset controls.
        for drone in self.drones:
            drone.controls = PlayerInput()

        # Test recovery.
        for drone in self.drones:
            car = self.game.cars[drone.index]

            # Handle time_on_ground
            if car.on_ground: 
                drone.time_on_ground += self.game.time_delta
            else:
                drone.time_on_ground = 0.0
            
            # Recovery time!
            if drone.time_on_ground < 0.2:
                if drone.recovery is None:
                    drone.recovery = Recovery(car)

                drone.recovery.step(self.game.time_delta)
                drone.controls = to_player_input(drone.recovery.controls)

                # Render things.
                self.renderer.begin_rendering(str(drone))
                self.renderer.draw_string_3d(car.position, 2, 2, str(drone.recovery.about_to_land), self.renderer.pink())
                self.renderer.draw_string_2d(100, 100, 5, 5, str(drone.recovery.aerial_turn.target), self.renderer.red())
                self.renderer.end_rendering()

            # Reset after recovery.
            else:
                drone.recovery = None
                drone.controls.throttle = 1.0

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

