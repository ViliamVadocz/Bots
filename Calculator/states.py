'''States.'''

from rlbot.agents.base_agent import SimpleControllerState

from utils import np, local, normalise, special_sauce

class BaseState:
    def __init__(self):
        self.expired = False

    @staticmethod
    def available(agent):
        return True

    def execute(self, agent):
        if not agent.r_active:
            self.expired = True


class Idle(BaseState):
    def execute(self, agent):
        self.expired = True


class Catch(BaseState):

    def __init__(self):
        super().__init__()
        self.target_pos = None
        self.target_time = None
    
    @staticmethod
    def available(agent):
        bounces, times = Catch.get_bounces(agent)
        if len(bounces) > 0:
            # If there are some bounces, calculate the distance to them.
            vectors = bounces - agent.player.pos
            distances = np.sqrt(np.einsum('ij,ij->i', vectors, vectors))
                
            # Check if the bounces are reachable (rough estimate).
            good_time = distances/1400 + 1 <= times
            return np.count_nonzero(good_time) > 0

        else:
            return False
        
    def execute(self, agent):
        super().execute(agent)

        # Checks if the ball has been hit recently.
        if agent.ball.last_touch.time_seconds + 0.1 > agent.game_time:
            self.expired = True
            
        elif self.target_pos is None:
            bounces, times = Catch.get_bounces(agent)
            vectors = bounces - agent.player.pos
            distances = np.sqrt(np.einsum('ij,ij->i', vectors, vectors))
            good_time = distances/1400 + 1 <= times
        
            self.target_pos = bounces[good_time][0]
            self.target_time = times[good_time][0]

        else:
            agent.ctrl = precise(agent, self.target_pos, self.target_time)


    @staticmethod
    def get_bounces(agent):
        # Looks for bounces in the ball predicion.
        z_pos = agent.ball.predict.pos[:,2]
        z_vel = agent.ball.predict.vel[:,2]
        bounce_bool = (z_vel[:-1] < z_vel[1:]) & (z_pos[:-1] < 93)
        bounces = agent.ball.predict.pos[:-1][bounce_bool]
        times = agent.ball.predict.time[:-1][bounce_bool]
        return bounces, times




def simple(agent, target, ctrl = SimpleControllerState()):
    # Calculates angle to target.
    local_target = local(agent.player.orient_m, agent.player.pos, target)
    angle = np.arctan2(local_target[1], local_target[0])

    # Steer using special sauce.
    ctrl.steer = special_sauce(angle, -5)

    # Throttle always 1.
    ctrl.throttle = 1

    # Handbrake if large angle.
    if abs(angle) > 1.85:
        ctrl.handbrake = True

    # Boost if small angle.
    elif abs(angle) < 0.5:
        ctrl.boost = 1

    return ctrl


def precise(agent, target, time, ctrl = SimpleControllerState()):
    # Calculates angle to target.
    local_target = local(agent.player.orient_m, agent.player.pos, target)
    angle = np.arctan2(local_target[1], local_target[0])

    # Steer using special sauce.
    ctrl.steer = special_sauce(angle, -5)

    # Throttle 1 but brakes at last moment.
    towards_target = target - agent.player.pos
    distance = np.linalg.norm(towards_target)
    vel = np.dot(towards_target / distance, agent.player.vel)

    ETA = distance/vel + agent.game_time

    ctrl.throttle = 1 if ETA > time else -1

    return ctrl