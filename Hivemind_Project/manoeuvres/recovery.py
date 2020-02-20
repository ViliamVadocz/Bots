from typing import Tuple

from rlutilities.linear_algebra import vec3, mat3, norm, normalize, look_at, angle_between, dot, cross
from rlutilities.simulation import Car, Input, Field, sphere
from rlutilities.mechanics import AerialTurn

from manoeuvres.manoeuvre import Manoeuvre

BOOST_HEIGHT_COMPENSATION = -1500
BOOST_ANGLE_DIFFERENCE_TOLERANCE = 0.6
MINIMUM_BOOST_DISTANCE = 500
SIMULATION_SPHERE_RADIUS = 40
GRAVITY = -650

# Thanks Darxeal! https://github.com/Darxeal/BotimusPrime
class Recovery(Manoeuvre):

    def __init__(self, car):
        super().__init__(car)

        self.about_to_land = False
        self.aerial_turn = AerialTurn(self.car)

    def step(self, dt: float):
        if self.about_to_land:
            _position, self.aerial_turn.target = self.find_landing_pos_and_orientation(dt)
            self.aerial_turn.step(dt)
            self.controls = self.aerial_turn.controls

        else:
            landing_pos, _orientation = self.find_landing_pos_and_orientation(dt)
            under_landing_pos = landing_pos + vec3(0, 0, BOOST_HEIGHT_COMPENSATION)
            landing_dir = normalize(under_landing_pos - self.car.position)

            self.aerial_turn.target = look_at(landing_dir, vec3(0, 0, 1))
            self.aerial_turn.step(dt)
            self.controls = self.aerial_turn.controls

            # Boost down when the angle is right.
            if angle_between(self.car.forward(), landing_dir) < BOOST_ANGLE_DIFFERENCE_TOLERANCE:
                self.controls.boost = True
            else:
                self.controls.boost = False

            # When nearing landing position start recovery.
            if norm(self.car.position - landing_pos) < clamp(norm(self.car.velocity), MINIMUM_BOOST_DISTANCE, 2300):
                self.about_to_land = True

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
            position += velocity * dt

            # Ignore first 10 frames because it might be ceiling.
            if i < 10:
                continue

            # Check for collisions with field.
            collision_normal = Field.collide(sphere(position, SIMULATION_SPHERE_RADIUS)).direction
            # Break out of simulation when collided.
            if norm(collision_normal) > 0.0:
                # Flatten velocity with regards to normal to get forward.
                forward = normalize(velocity - dot(velocity, collision_normal) * collision_normal)
                left = normalize(cross(collision_normal, forward))
                break

        # If we don't break we return the current orientation.
        else: return position, self.car.orientation

        return position, three_vec3_to_mat3(forward, left, collision_normal)


def three_vec3_to_mat3(f, l, u):
    return mat3(f[0], l[0], u[0],
                f[1], l[1], u[1],
                f[2], l[2], u[2])

def clamp(value, minimum, maximum):
    return max(min(value, maximum), minimum)