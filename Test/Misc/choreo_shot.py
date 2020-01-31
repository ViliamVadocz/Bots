import math
import time
import keyboard

from rlbot.utils.structures.game_interface import GameInterface
from rlbot.utils.logging_utils import get_logger
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator

CAR_LOCATION = Vector3(-2500, -4000, 20)
BALL_LOCATION = Vector3(-3140, -1940, 93)

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
            car_states = {
                0: CarState(physics=Physics(
                    location=CAR_LOCATION, 
                    velocity=Vector3(0,0,0), 
                    rotation=Rotator(0, 3*math.pi/4, 0),
                    angular_velocity=Vector3(0,0,0)
                    ))}
                    
            # Reset ball position.
            ball_state = BallState(Physics(
                location=BALL_LOCATION, 
                velocity=Vector3(0,0,0),
                rotation=Rotator(0,0,0),
                angular_velocity=Vector3(0,0,0)
                ))

            game_state = GameState(ball=ball_state, cars=car_states)
            self.game_interface.set_game_state(game_state)

if __name__ == "__main__":
    obv = Observer()