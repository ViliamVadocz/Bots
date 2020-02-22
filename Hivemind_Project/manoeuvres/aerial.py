from math import inf

from rlutilities.linear_algebra import vec3, norm, normalize, angle_between, dot
from rlutilities.mechanics import Aerial as RLUAerial
from rlutilities.mechanics import Drive
from rlutilities.simulation import Car, Input

from manoeuvres.manoeuvre import Manoeuvre

HANDBRAKE_MINIMUM_ANGLE = 2.0
ANGLE_DIFFERENCE_BEFORE_JUMP = 0.1
SPEED_PERCENTAGE_BEFORE_JUMP = 0.7
GIVE_UP_SPEED_NEEDED = 2200
MINIMUM_TARGET_DISTANCE = 100

HOLD_FIRST_JUMP_TIME = 0.2
TIME_BETWEEN_HOLDING_JUMP = 0.1
HOLD_SECOND_JUMP_TIME = 0.05


class Aerial(Manoeuvre):

    def __init__(self, car: Car, target: vec3, game_time: float, arrival_time_from_now: float):
        super().__init__(car)

        self.target = target
        self.arrival_time = arrival_time_from_now
        self.ready_to_jump = False
        self.time_since_jumped = -inf
        self.timer = 0.0

        # RLU Mechanic setup
        self.aerial = RLUAerial(car)
        self.aerial.target = self.target
        self.aerial.arrival_time = game_time + arrival_time_from_now
        self.drive = Drive(car)
        self.drive.target = self.target

    def step(self, dt: float):

        time_left = self.arrival_time - self.timer
        flat_difference = self.target - self.car.position
        flat_difference[2] = 0.0
        speed_needed = norm(flat_difference) / time_left

        # Do the aerial.
        if self.time_since_jumped > HOLD_FIRST_JUMP_TIME + TIME_BETWEEN_HOLDING_JUMP + HOLD_SECOND_JUMP_TIME:
            self.aerial.step(dt)
            self.controls = self.aerial.controls

        # Fast aerial jump.
        elif self.ready_to_jump:
            self.controls = Input()
            self.controls.boost = True

            if self.time_since_jumped < HOLD_FIRST_JUMP_TIME:
                self.controls.jump = True
                self.controls.pitch = 1.0

            elif self.time_since_jumped < HOLD_FIRST_JUMP_TIME + TIME_BETWEEN_HOLDING_JUMP:
                self.controls.jump = False
                self.controls.pitch = 1.0

            else:
                self.controls.jump = True
                self.controls.pitch = 0.0

            self.time_since_jumped += dt

        else:
            # Align yourself before jumping.
            direction_to_target = normalize(flat_difference)
            speed_in_direction = dot(direction_to_target, self.car.velocity)
            angle = angle_between(flat_difference, self.car.velocity)

            self.drive.speed = speed_needed
            self.drive.step(dt)
            self.controls = self.drive.controls
            if angle > HANDBRAKE_MINIMUM_ANGLE:
                self.controls.handbrake = True
                self.controls.throttle = 1.0
            else:
                self.controls.handbrake = False

            # If angle and speed is good, jump.
            if angle < ANGLE_DIFFERENCE_BEFORE_JUMP \
                    and speed_in_direction / speed_needed > SPEED_PERCENTAGE_BEFORE_JUMP:
                self.ready_to_jump = True
                self.time_since_jumped = 0.0

        self.timer += dt
        time_left = self.arrival_time - self.timer
        self.finished = time_left <= 0.0 or speed_needed > GIVE_UP_SPEED_NEEDED or norm(self.car.position - self.target) < MINIMUM_TARGET_DISTANCE
