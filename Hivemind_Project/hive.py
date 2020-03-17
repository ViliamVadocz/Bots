from typing import Dict
from enum import Enum

from rlbot.agents.hivemind.python_hivemind import PythonHivemind
from rlbot.utils.structures.bot_input_struct import PlayerInput
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction
from rlbot.utils.rendering.rendering_manager import RenderingManager

from rlutilities.linear_algebra import vec2, vec3, dot, norm, normalize, look_at, angle_between
from rlutilities.mechanics import Drive, AerialTurn
from rlutilities.simulation import Game

from util.drone import Drone
from util.general import team_sign, to_player_input
from util.goal_detector import find_future_goal
from util.vector_maths import dist, flat

from manoeuvres.recovery import Recovery
from manoeuvres.half_flip import HalfFlip
from manoeuvres.aerial import Aerial
from manoeuvres.slow_to_pos import SlowToPos

RIGHT_POS = vec3(-900, -4900, 0)
MIDDLE_POS = vec3(0, -5300, 0)
LEFT_POS = vec3(900, -4900, 0)
DEFENCE_POSITIONS = [RIGHT_POS, MIDDLE_POS, LEFT_POS]
IN_FRONT_OF_OWN_GOAL = vec3(0, -5000, 0)


class Overmind(PythonHivemind):
    verbose = True

    def initialize_hive(self, packet: GameTickPacket) -> None:
        if self.verbose:
            self.logger.setLevel("DEBUG")
        else:
            self.logger.setLevel("ERROR")


        self.logger.info('The Swarm Awakens...')

        # Find out team by looking at packet.
        # drone_indices is a set, so you cannot just pick first element.
        my_index = next(iter(self.drone_indices))
        self.team = packet.game_cars[my_index].team
        self.sign = team_sign(self.team)

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
            drone.recovery = None
            drone.half_flip = None
            drone.aerial = None
            drone.slow_to_pos = None
            drone.aerial_turn = AerialTurn(car)
            drone.car = car

    def get_outputs(self, packet: GameTickPacket) -> Dict[int, PlayerInput]:

        self.update_game(packet)
        dt = self.game.time_delta

        # Handle time on ground.
        for drone in self.drones:
            if drone.car.on_ground:
                drone.time_on_ground += dt
                drone.time_off_ground = 0.0
            else:
                drone.time_on_ground = 0.0
                drone.time_off_ground += dt

        # Ball prediction.
        ball_prediction: BallPrediction = self.get_ball_prediction_struct()
        future_goal = find_future_goal(ball_prediction)
        needs_saving = False
        if future_goal is not None:
            if future_goal.team == self.team:
                needs_saving = True

        if self.verbose:
            self.render_ball_prediction(ball_prediction)

        # Reset controls.
        for drone in self.drones:
            drone.controls = PlayerInput()        
        
        # Sort drones right to left.
        self.drones.sort(key=lambda drone: self.sign * drone.car.position[0])

        if needs_saving:
            if self.verbose:
                self.render_target(future_goal.position)

            going = None
            for drone in self.drones:
                if drone.ready:
                    # TODO Calculate soonest intercept for each drone
                    pass

            # if still nothing, consider not ready.


        # Go back to goal.
        for i, drone in enumerate(self.drones):
            drone.ready = False
            defence_pos = DEFENCE_POSITIONS[i] * self.sign
            if drone.slow_to_pos is None:
                drone.slow_to_pos = SlowToPos(drone.car, defence_pos)

            if dist(drone.car.position, defence_pos) > 200:
                # Recovery.
                if drone.time_on_ground < 0.2 and drone.slow_to_pos.half_flip is None:
                    if drone.recovery is None:
                        drone.recovery = Recovery(drone.car)
                    drone.recovery.step(dt)
                    drone.controls = to_player_input(drone.recovery.controls)

                # Go to pos.
                else:
                    if drone.recovery is not None:
                        drone.recovery = None
                    
                    drone.slow_to_pos.target = defence_pos
                    drone.slow_to_pos.step(dt)
                    drone.controls = to_player_input(drone.slow_to_pos.controls)

            else:
                # If speed is low, jump and turn.
                speed_2D = norm(vec2(drone.car.velocity))
                if speed_2D < 100:
                    car_to_look_pos = flat(self.sign * IN_FRONT_OF_OWN_GOAL - drone.car.position)

                    drone.aerial_turn.target = look_at(car_to_look_pos, vec3(0, 0, 1))
                    drone.aerial_turn.step(dt)
                    drone.controls = to_player_input(drone.aerial_turn.controls)

                    if angle_between(drone.car.forward(), normalize(car_to_look_pos)) > 0.3:
                        if drone.time_on_ground > 0.2 or (drone.car.jumped and drone.time_off_ground < 0.05):
                            drone.controls.jump = True

                    else:
                        drone.ready = True

                # Go to pos.
                else:
                    drone.slow_to_pos.target = defence_pos
                    drone.slow_to_pos.step(dt)
                    drone.controls = to_player_input(drone.slow_to_pos.controls)

        return self.make_drone_controls_dict()

    def update_game(self, packet):
        self.game.read_game_information(
            packet,
            self.field_info
        )

    def make_drone_controls_dict(self) -> Dict[int, PlayerInput]:
        return {drone.index: drone.controls for drone in self.drones}


    def render_ball_prediction(self, ball_prediction: BallPrediction):
        r: RenderingManager = self.renderer
        r.begin_rendering(f"{self} - ball prediction")
        r.draw_polyline_3d([step.physics.location for step in ball_prediction.slices[:ball_prediction.num_slices:20]], r.cyan())
        r.end_rendering()

    def render_target(self, target):
        r: RenderingManager = self.renderer
        r.begin_rendering(f"{self} - target {target}")
        r.draw_rect_3d(target, 10, 10, True, r.red())
        r.end_rendering()