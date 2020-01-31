from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator

import numpy as np
from utils import Car, Ball, a3l, a3r, a3v, orient_matrix, local, world, angle_between_vectors, cap

class TestBot(BaseAgent):

    def initialize_agent(self):
        self.player  = Car(self.index, self.team, self.name)
        self.ball = Ball()


    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        """Runs every tick. Returns the bot controller.
        
        Arguments:
            packet {GameTickPacket} -- The information packet from the game.
        
        Returns:
            SimpleControllerState -- The controller for the bot.
        """
        # Run some light preprocessing.
        self.process(packet)

        # Reset exercise when angle is small.
        front = world(self.player.orient_m, np.zeros(3), a3l([1, 0, 0]))
        angle = angle_between_vectors(front, self.ball.pos - self.player.pos)
        #print(angle)
        self.keep_ball_and_car_floating(new_orientation=(abs(angle) < 0.05))

        return orient_towards_ball(self)

    def process(self, packet: GameTickPacket):
        """Simplified preprocessing which just takes care of the car info that I need.
        
        Arguments:
            packet {GameTickPacket} -- The information packet from the game.
        """
        self.player.rot      = a3r(packet.game_cars[self.player.index].physics.rotation)
        self.player.ang_vel  = a3v(packet.game_cars[self.player.index].physics.angular_velocity)
        self.player.orient_m = orient_matrix(self.player.rot)
        self.ball.pos = a3l([0, 500, 1000])
        

    def keep_ball_and_car_floating(self, new_orientation=False):
        ball_state = BallState(physics=Physics(location=Vector3(0, 500, 1000)))
        if new_orientation:
            print('new orientation!')
            new_rot = Rotator(np.pi*np.random.rand()-(np.pi/2), 2*np.pi*np.random.rand()-np.pi, 2*np.pi*np.random.rand()-np.pi)
            car_state = {self.index : CarState(physics=Physics(location=Vector3(0, 0, 1000), velocity=Vector3(0, 0, 0), rotation = new_rot, angular_velocity = Vector3(0, 0, 0)))}
        else:
            car_state = {self.index : CarState(physics=Physics(location=Vector3(0, 0, 1000), velocity=Vector3(0, 0, 0)))}
        game_state = GameState(ball=ball_state, cars=car_state)
        self.set_game_state(game_state)

def orient_towards_ball(agent):
    # Reset ctrl.
    ctrl = SimpleControllerState()
        
    # TODO
    to_ball = local(agent.player.orient_m, agent.player.pos, agent.ball.pos)
    yaw_diff = np.arctan2(to_ball[1], to_ball[0])
    pitch_diff = np.arctan2(to_ball[2], to_ball[0])
    roll_diff = np.arctan2(to_ball[2], to_ball[1])
    
    ctrl.yaw = cap(yaw_diff, -1, 1)
    ctrl.pitch = cap(pitch_diff, -1 , 1)
    #ctrl.roll = cap(roll_diff, -1, 1)

    return ctrl