from typing import Tuple

from rlutilities.linear_algebra import vec3, mat3, norm, normalize, look_at, angle_between, dot, cross, euler_to_rotation
from rlutilities.mechanics import AerialTurn
from rlutilities.simulation import Car, Field, sphere

from manoeuvres.manoeuvre import Manoeuvre
from utils.random import three_vec3_to_mat3, clamp

BOOST_HEIGHT_COMPENSATION = -2000
BOOST_ANGLE_DIFFERENCE_TOLERANCE = 0.5
MINIMUM_RECOVERY_TIME = 0.5
# WAVE_DASH_PITCH_UP = 0.3
# WAVE_DASH_TIME = 0.18
SIMULATION_SPHERE_RADIUS = 40
SIMULATION_DT = 1 / 60
GRAVITY = -650


class Recovery(Manoeuvre):

    def __init__(self, car: Car, jump_when_upside_down=True):
        super().__init__(car)

        self.jump_when_upside_down = jump_when_upside_down
        self.about_to_land = False

        # RLU Mechanic setup
        self.aerial_turn = AerialTurn(self.car)

    def step(self, dt: float):
        self.controls.boost = False

        # Prepare for landing.
        if self.about_to_land:
            _landing_pos, orientation = self.find_landing_pos_and_orientation(SIMULATION_DT)

            self.aerial_turn.target = orientation
            self.aerial_turn.step(dt)
            self.controls = self.aerial_turn.controls

        # Boost down.
        else:
            landing_pos, _orientation = self.find_landing_pos_and_orientation(SIMULATION_DT)
            under_landing_pos = landing_pos + vec3(0, 0, BOOST_HEIGHT_COMPENSATION)
            landing_dir = normalize(under_landing_pos - self.car.position)

            self.aerial_turn.target = look_at(landing_dir, vec3(0, 0, 1))
            self.aerial_turn.step(dt)
            self.controls = self.aerial_turn.controls

            # Boost down when the angle is right.
            self.controls.boost = angle_between(
                self.car.forward(), landing_dir) < BOOST_ANGLE_DIFFERENCE_TOLERANCE

            # When nearing landing position start recovery.
            if self.car.boost == 0.0 or landing_pos[2] > 1000:
                self.about_to_land = True
            else:
                # In else so that we don't calculate if we don't have to.
                distance = norm(self.car.position - landing_pos)
                speed = norm(self.car.velocity)
                if speed > 2200 or (speed != 0.0 and distance / speed < MINIMUM_RECOVERY_TIME):
                    self.about_to_land = True

        # If the car is upside down and has wheel contact, jump.
        if self.jump_when_upside_down and \
                self.car.on_ground and dot(self.car.up(), vec3(0, 0, 1)) < -0.95:
            self.controls.jump = True
            self.about_to_land = False

        # Prevent turtling.
        self.controls.throttle = 1.0
        # Smoother landing.
        self.controls.handbrake = True

    def find_landing_pos_and_orientation(self, dt, num_points=200) -> Tuple[vec3, mat3]:
        """Simulate the car until it lands and return its final position and desired orientation."""
        position = vec3(self.car.position)
        velocity = vec3(self.car.velocity)
        gravity = vec3(0, 0, GRAVITY)

        for i in range(num_points):
            velocity += gravity * dt
            speed = norm(velocity)
            if speed > 2300:
                velocity = velocity/speed * 2300
            position += velocity * dt

            # Ignore first 10 frames because it might be ceiling.
            if i < 10:
                continue

            # Check for collisions with field.
            collision_normal = Field.collide(
                sphere(position, SIMULATION_SPHERE_RADIUS)).direction
            # Break out of simulation when collided.
            if norm(collision_normal) > 0.0:
                # Flatten velocity with regards to normal to get forward.
                forward = normalize(
                    velocity - dot(velocity, collision_normal) * collision_normal)
                left = normalize(cross(collision_normal, forward))
                break

        # If we don't break we return the current orientation.
        else:
            print("USING CAR'S CURRENT ORIENTATION") # XXX debugging
            return position, self.car.orientation

        return position, three_vec3_to_mat3(forward, left, collision_normal)
