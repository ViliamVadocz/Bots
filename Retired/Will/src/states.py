from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from util.orientation import Orientation, relative_location
from util.aerial import AerialStep, LineUpForAerialStep
from util.drive import steer_toward_target
from util.goal_detector import find_future_goal
from util.sequence import Sequence, ControlStep
from util.spikes import SpikeWatcher
from util.vec import Vec3
from util.drive import limit_to_safe_range

from math import copysign, atan2

class BaseState:

    def __init__(self):
        self.active = True

    @staticmethod
    def available(agent, packet: GameTickPacket) -> bool:
        return True

    def execute(self, agent, packet: GameTickPacket) -> SimpleControllerState:
        self.active = False
        return SimpleControllerState()


class Kickoff(BaseState):
    
    @staticmethod
    def available(agent, packet: GameTickPacket) -> bool:
        ball = Vec3(packet.game_ball.physics.location)
        return ball.x == 0.0 and ball.y == 0.0

    def execute(self, agent, packet: GameTickPacket) -> SimpleControllerState:
        self.active = False
        return SimpleControllerState()
    

class Defence(BaseState):
    target_location = Vec3(0, 5200, 20)

    @staticmethod
    def available(agent, packet: GameTickPacket) -> bool:
        self.active = False
        agent.spike_watcher.carrying_car.team == agent.team and agent.spike_watcher.carrying_car.team != packet.game_cars[agent.index]

        return move_to_pos(agent, self.target_location)
    

class WallThing(BaseState):

    def __init__(self):
        self.active = True
        self.on_wall = False

    @staticmethod
    def available(agent, packet: GameTickPacket) -> bool:
        return agent.spike_watcher.carrying_car == packet.game_cars[agent.index] and packet.game_cars[agent.index].physics.location.y > -3000

    def execute(self, agent, packet: GameTickPacket) -> SimpleControllerState:
        my_car = packet.game_cars[agent.index]

        if agent.spike_watcher.carrying_car != my_car:
            self.active = False

        my_car = packet.game_cars[agent.index]
        pos = Vec3(my_car.physics.location)
        
        self.on_wall = my_car.has_wheel_contact and Orientation(my_car.physics.rotation).up.z < 0.5

        if self.on_wall:
            target_location = Vec3(0, -5300, 500)
            
        else:
            target_location = Vec3(copysign(4100, pos.x), pos.y, 500)


        ctrl = move_to_pos(my_car, target_location)

        ctrl.pitch = -1.0

        return ctrl


class GetBoost(BaseState):

    def __init__(self):
        self.boost_selected = False
        self.chosen_pad = None
        super().__init__()
    
    @staticmethod
    def available(agent, packet: GameTickPacket) -> bool:
        low_boost = packet.game_cars[agent.index].boost < 20
        car_pos = Vec3(packet.game_cars[agent.index].physics.location)
        ball_pos = Vec3(packet.game_ball.physics.location)
        ball_away = (ball_pos - car_pos).length() + 1000 < (Vec3(closest_pad(agent, packet).location) - car_pos).length()

        return low_boost and ball_away and not agent.spike_watcher.carrying_car == packet.game_cars[agent.index]

    def execute(self, agent, packet: GameTickPacket) -> SimpleControllerState:
        my_car = packet.game_cars[agent.index]
        car_pos = Vec3(my_car.physics.location)
        ball_pos = Vec3(packet.game_ball.physics.location)
        self.active = packet.game_cars[agent.index].boost > 80 or (ball_pos - car_pos).length() < 300 or not agent.spike_watcher.carrying_car == packet.game_cars[agent.index]

        if not self.boost_selected:
            print('hey')
            self.chosen_pad = closest_pad(agent, packet)
            self.boost_selected = True

        else:
            print('hi')
            return move_to_pos(my_car, Vec3(self.chosen_pad.location))

def closest_pad(agent, packet):
    car_pos = Vec3(packet.game_cars[agent.index].physics.location)
    closest = agent.active_pads[0]
    for pad in agent.active_pads:
        if (Vec3(pad.location) - car_pos).length() < (Vec3(closest.location) - car_pos).length():
            closest = pad

    return closest


class Simple(BaseState):
    
    def execute(self, agent, packet: GameTickPacket) -> SimpleControllerState:
        self.active = False

        my_car = packet.game_cars[agent.index]
        
        if agent.spike_watcher.carrying_car == my_car:
            target_location = Vec3(0, -5300, 100)
        else:
            target_location = Vec3(packet.game_ball.physics.location).flat()

        ctrl = move_to_pos(my_car, target_location)

        return ctrl


def move_to_pos(car, target: Vec3) -> SimpleControllerState:
    ctrl = SimpleControllerState()
    ctrl.steer = steer_toward_target(car, target)

    orientation = Orientation(car.physics.rotation)
    relative = relative_location(Vec3(car.physics.location), orientation, target)

    angle = atan2(relative.y, relative.x)

    close = relative.flat().length() < 200
    if close:
        ctrl.throttle = 1.0 if abs(relative.x) > 100 else limit_to_safe_range(relative.x / 10)
        ctrl.jump = relative.z > 200
        ctrl.boost = ctrl.throttle > 0.9

    else:
        ctrl.throttle = 1.0
        ctrl.boost = True

    if angle > 1.65:
        ctrl.handbrake = True

    # We're upside down
    if orientation.up.length() < 0.0:
        ctrl.throttle = 1.0

    return ctrl
