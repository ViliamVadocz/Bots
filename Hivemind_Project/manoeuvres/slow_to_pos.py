from math import atan2, pi, exp

from rlbot.utils.structures.bot_input_struct import PlayerInput

from rlutilities.linear_algebra import vec3, norm, dot
from rlutilities.simulation import Car

from manoeuvres.manoeuvre import Manoeuvre
from util.vector_maths import dist
from util.general import clamp


class SlowToPos(Manoeuvre):

    def __init__(self, car: Car, target: vec3):
        super().__init__(car)
        self.target = target

    def step(self, dt: float):
        # Some pre-processing.
        car_to_target = self.target - self.car.position
        distance = norm(car_to_target)
        speed = norm(self.car.velocity)

        relative = dot(car_to_target, self.car.orientation)
        angle = atan2(relative[1], relative[0])
        absolute_angle = abs(angle)

        forward_speed = dot(self.car.velocity, self.car.forward())

        # Reset controls.
        self.controls = PlayerInput()

        if distance > 100:
            self.finished = False

            # A simple PD controller to stop at target.
            throttle_magnitude = clamp(0.3*distance - 0.2*speed, -1.0, 1.0)

            # Going backwards.
            if forward_speed < 1600 and absolute_angle > 2.5:
                # Rotates angle pi radians to face backwards.
                adjusted_angle = pi - angle if angle > 0.0 else -(pi + angle)
                self.controls.throttle = -throttle_magnitude
                self.controls.handbrake = abs(adjusted_angle) > 1.7
                self.controls.steer = angle_to_steer(adjusted_angle)

            else:
                self.controls.throttle = throttle_magnitude
                self.controls.handbrake = absolute_angle > 1.7
                self.controls.steer = angle_to_steer(angle)
                self.controls.boost = throttle_magnitude >= 0.99 and absolute_angle < 0.5 and forward_speed < 2200
        
        else:
            self.finished = True


def angle_to_steer(angle: float) -> float:
    """Modified sigmoid function."""
    return 2 / (1 + exp(-6 * angle)) - 1
    