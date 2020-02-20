# import math
import time
import keyboard

from rlbot.utils.structures.game_interface import GameInterface
from rlbot.utils.logging_utils import get_logger
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator

CAR_STATE = {0: CarState(physics=Physics(
                location=Vector3(-2000, -3000, 500), 
                velocity=Vector3(100, 100, 2300), 
                rotation=Rotator(0, 0, 0),
                angular_velocity=Vector3(0, 0, 0)
                ))}

BALL_STATE = BallState(Physics(
                location=Vector3(0, 0, 93), 
                velocity=Vector3(0, 0, 0),
                rotation=Rotator(0, 0, 0),
                angular_velocity=Vector3(0, 0, 0)
                ))


RESET_KEY = 'r'

class Observer():
    def __init__(self):
        self.game_interface = GameInterface(get_logger("observer"))
        self.game_interface.load_interface()
        self.game_interface.wait_until_loaded()
        self.main()

    def main(self):
        while True:

            time.sleep(0.1)

            if not keyboard.is_pressed(RESET_KEY):
                continue
            
            # Reset car position.
            car_states = CAR_STATE
                    
            # Reset ball position.
            ball_state = BALL_STATE

            game_state = GameState(ball=ball_state, cars=car_states)
            self.game_interface.set_game_state(game_state)

if __name__ == "__main__":
    obv = Observer()