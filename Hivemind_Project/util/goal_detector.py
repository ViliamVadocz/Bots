
from dataclasses import dataclass

from rlbot.utils.structures.ball_prediction_struct import BallPrediction

from rlutilities.linear_algebra import vec3

# field length(5120) + ball radius(93) = 5213 however that results in false positives
GOAL_THRESHOLD = 5235

# We will jump this number of frames when looking for a moment where the ball is inside the goal.
# Big number for efficiency, but not so big that the ball could go in and then back out during that
# time span. Unit is the number of frames in the ball prediction, and the prediction is at 60 frames per second.
COARSE_SEARCH_INCREMENT = 20


@dataclass
class FutureGoal:
    location: vec3
    velocity: vec3
    time: float
    team: int


def find_future_goal(ball_prediction: BallPrediction):
    # Do course search.
    for coarse_index in range(0, ball_prediction.num_slices, COARSE_SEARCH_INCREMENT):
        step = ball_prediction.slices[coarse_index]
        position = step.physics.location
        # If found, do a thorough search.
        if abs(position.y) >= GOAL_THRESHOLD:
            go_back = max(0, coarse_index - COARSE_SEARCH_INCREMENT)
            for j in range(go_back, coarse_index):
                step = ball_prediction.slices[j]
                position = step.physics.location
                if abs(position.y) >= GOAL_THRESHOLD:
                    vel = step.physics.velocity
                    return FutureGoal(
                        vec3(position.x, position.y, position.z),
                        vec3(vel.x, vel.y, vel.z),
                        step.game_seconds,
                        int(position.y > 0),
                    )
    return None
