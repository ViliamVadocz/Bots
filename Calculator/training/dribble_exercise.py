from dataclasses import dataclass, field
from pathlib import Path
from math import pi

from dribble_grader import DribbleGrader

from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.matchconfig.match_config import Team, PlayerConfig 

from rlbottraining.training_exercise import TrainingExercise, Playlist
from rlbottraining.grading.grader import Grader
from rlbottraining.rng import SeededRandomNumberGenerator

@dataclass
class DribbleDrop(TrainingExercise):
    grader : Grader = field(default_factory=DribbleGrader)

    def make_game_state(self, rng: SeededRandomNumberGenerator) -> GameState:
        car_state = CarState(
            boost_amount=100,
            physics=Physics(
                location=Vector3(rng.n11()*1000, 0, 20),
                velocity=Vector3(0, 0, 0),
                rotation=Rotator(0, pi / 2, 0),
                angular_velocity=Vector3(0, 0, 0)
                )
            )

        ball_state = BallState(
            Physics(
                location=Vector3(0, 1000, 1000),
                velocity=Vector3(0, -500, 500)
                )
            )

        game_state = GameState(ball=ball_state, cars={0: car_state})
        return game_state


@dataclass
class DribbleRoll(TrainingExercise):
    grader : Grader = field(default_factory=DribbleGrader)
    
    def make_game_state(self, rng: SeededRandomNumberGenerator) -> GameState:
        car_state = CarState(
            boost_amount=100,
            physics=Physics(
                location=Vector3(0, -3500, 20),
                velocity=Vector3(0, 0, 0),
                rotation=Rotator(0, -pi/2, 0),
                angular_velocity=Vector3(0, 0, 0)
                )
            )

        ball_state = BallState(
            Physics(
                location=Vector3(0, -4000, 100),
                velocity=Vector3(700*rng.n11(), 700*rng.n11(), 0)
                )
            )

        game_state = GameState(ball=ball_state, cars={0: car_state})
        return game_state


def make_default_playlist() -> Playlist:
    exercises = [DribbleRoll('Dribble Roll'), DribbleDrop('Dribble Drop')]

    for ex in exercises:
        ex.match_config.player_configs = [
            PlayerConfig.bot_config(Path(__file__).absolute().parent.parent / 'Calculator.cfg', Team.BLUE)
        ]

    return exercises






    