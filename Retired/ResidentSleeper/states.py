import numpy as np

from rlbot.agents.base_agent import SimpleControllerState

from utils import a3l, local, normalise, cap, team_sign, special_sauce, linear_predict

blue_inside_goal = a3l([0, -5120, 0])
orange_inside_goal = a3l([0, 5120, 0])

kickoff_positions = np.array([
    [-1952, -2464, 0], # r_corner
    [ 1952, -2464, 0], # l_corner
    [ -256, -3840, 0], # r_back
    [  256, -3840, 0], # l_back
    [  0.0, -4608, 0]  # centre
])

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


class SimplePush(BaseState):

    def execute(self, agent):
        goal = orange_inside_goal * team_sign(agent.team) 

        # Calculate distance to ball.
        distance = np.linalg.norm(agent.ball.pos - agent.player.pos)

        # Find directions based on where we want to hit the ball.
        direction_to_hit = normalise(goal - agent.ball.pos)
        perpendicular_to_hit = np.cross(direction_to_hit, a3l([0,0,1]))

        # Calculating component lengths and multiplying with direction.
        perpendicular_component = 2*perpendicular_to_hit * cap(np.dot(perpendicular_to_hit, agent.ball.pos), -distance/3, distance/3)/3
        in_direction_component = -direction_to_hit * distance/3

        # Combine components to get a drive target.
        target = agent.ball.pos + in_direction_component + perpendicular_component

        agent.ctrl = simple(agent.player, target)
        agent.ctrl.boost = False

        # Dodge when far away..
        if agent.player.pos[2] < 20 and distance > 1500 and (1000 < np.dot(normalise(agent.ball.pos-agent.player.pos), agent.player.vel) < 2000):
            self.expired = True
            agent.state = Dodge(agent.ball.pos)

        self.expired = True
        super().execute(agent)


class Kickoff(BaseState):

    def __init__(self):
        super().__init__()
        self.kickoff_pos = None
        self.timer = 0.0
        self.dodge = None

    @staticmethod
    def available(agent):
        return agent.ball.pos[0] == 0 and agent.ball.pos[1] == 0

    def execute(self, agent):
        # If the kickoff pause ended and the ball has been touched recently, expire.
        if agent.ball.pos[0] != 0 or agent.ball.pos[1] != 0 or self.timer > 3.0:
            self.expired = True

        if self.kickoff_pos is None:
            # Find closest kickoff position.
            vectors = kickoff_positions * team_sign(agent.team) - agent.player.pos
            distances = np.sqrt(np.einsum('ij,ij->i', vectors, vectors))
            self.kickoff_pos = np.where(distances == np.amin(distances))[0][0]
            
        team = team_sign(agent.team)
        side = 1 if self.kickoff_pos in (0,2) else -1
        
        # Corner
        if self.kickoff_pos in (0,1):
            if self.timer < 0.5:
                target = a3l([-800*side, 0, 0]) * team
                agent.ctrl = simple(agent.player, target)

            else:
                if self.dodge is None: 
                    self.dodge = Dodge(a3l([0, -2500, 0])*team)
                    agent.ctrl.boost = True

                else:
                    self.dodge.execute(agent)
                    agent.ctrl.boost = True
                    #if self.dodge.expired: self.dodge = None

        # Back
        elif self.kickoff_pos in (2,3):
            distance = np.linalg.norm(agent.ball.pos - agent.player.pos)
            if np.linalg.norm(agent.player.vel) == 0:
                ETA = 100
            else:
                ETA = distance / np.linalg.norm(agent.player.vel)

            if distance > 3200:
                target = a3l([0, -2700, 70]) * team_sign(agent.team)
            else:
                target = agent.ball.pos

            # Dodge if close.
            if self.dodge is None:
                if ETA < 0.4: self.dodge = Dodge(agent.ball.pos)
                agent.ctrl = simple(agent.player, target)
            else:
                self.dodge.execute(agent)

        # Centre
        else:
            distance = np.linalg.norm(agent.ball.pos - agent.player.pos)
            if np.linalg.norm(agent.player.vel) == 0:
                ETA = 100
            else:
                ETA = distance / np.linalg.norm(agent.player.vel)

            # Dodge if close.
            if self.dodge is None:
                if ETA < 0.4: self.dodge = Dodge(agent.ball.pos)
                agent.ctrl = simple(agent.player, agent.ball.pos)
            else:
                self.dodge.execute(agent)


        self.timer += agent.dt
        super().execute(agent)


class Demo(BaseState):

    @staticmethod
    def available(agent):
        # Finds closest opponent.
        closest_opponent = agent.opponents[0]
        for opponent in agent.opponents:
            distance = np.linalg.norm(agent.player.pos - opponent.pos)
            if distance < np.linalg.norm(agent.player.pos - closest_opponent.pos):
                closest_opponent = opponent
        closest_op_distance = np.linalg.norm(agent.player.pos - closest_opponent.pos)

        return (closest_op_distance < 1000 and agent.player.boost > 50)

    def execute(self, agent):
        # Finds closest opponent.
        closest_opponent = agent.opponents[0]
        for opponent in agent.opponents:
            if opponent.dead: continue
            distance = np.linalg.norm(agent.player.pos - opponent.pos)
            if distance < np.linalg.norm(agent.player.pos - closest_opponent.pos):
                closest_opponent = opponent
        
        closest_op_distance = np.linalg.norm(agent.player.pos - closest_opponent.pos)
        time_left = closest_op_distance/np.linalg.norm(agent.player.vel) + 0.1
        opponent_predict = linear_predict(closest_opponent.pos, closest_opponent.vel, agent.game_time, time_left)

        agent.ctrl = simple(agent.player, opponent_predict.pos[-1])

        if closest_op_distance > 1500 or np.linalg.norm(agent.player.vel) < 500:
            self.expired = True


class Dodge(BaseState):

    def __init__(self, target_pos):
        super().__init__()
        self.target_pos = target_pos
        self.timer = 0.0

    def execute(self, agent):
        if self.timer < 0.1:
            agent.ctrl.jump = True
        elif self.timer < 0.2:
            agent.ctrl.jump = False
            agent.ctrl.pitch = -1
        elif self.timer < 0.3:
            local_target = local(agent.player.orient_m, agent.player.pos, self.target_pos)
            direction = normalise(local_target)

            agent.ctrl.jump = True
            agent.ctrl.pitch = -direction[0]
            agent.ctrl.yaw = direction[1]        
        else:
            self.expired = True

        self.timer += agent.dt
        super().execute(agent)


class GetBoost(BaseState):

    def __init__(self):
        super().__init__()
        self.target_pad = None

    @staticmethod
    def available(agent):
        if agent.player.boost < 30:
            ball_distance = np.linalg.norm(agent.ball.pos - agent.player.pos)
            for pad in agent.l_pads:
                if pad.active:
                    pad_distance = np.linalg.norm(pad.pos - agent.player.pos)
                    if pad_distance < 500:
                        return True
                    elif pad_distance + 700 < ball_distance:
                        return True

        return False

    def execute(self, agent):

        if self.target_pad is None:
            ball_distance = np.linalg.norm(agent.ball.pos - agent.player.pos)
            for pad in agent.l_pads:
                if pad.active:
                    pad_distance = np.linalg.norm(pad.pos - agent.player.pos)
                    if pad_distance < 500:
                        self.target_pad = pad
                        break
                    elif pad_distance + 700 < ball_distance:
                        self.target_pad = pad
                        break
                            
        # If still nothing, expire.
        if self.target_pad is None:
            self.expired = True

        if agent.player.boost >= 80 or not self.target_pad.active:
            self.expired = True
            
        # Dodge when far away.
        if agent.player.pos[2] < 20 and np.linalg.norm(self.target_pad.pos-agent.player.pos) > 1500 \
            and (1000 < np.dot(normalise(agent.ball.pos-agent.player.pos), agent.player.vel) < 2000):
            self.expired = True
            agent.state = Dodge(agent.ball.pos)

        agent.ctrl = simple(agent.player, self.target_pad.pos)
        super().execute(agent)


def simple(player, target):
    ctrl = SimpleControllerState()

    # Calculates angle to target.
    local_target = local(player.orient_m, player.pos, target)
    angle = np.arctan2(local_target[1], local_target[0])

    # Steer using special sauce.
    ctrl.steer = special_sauce(angle, -5)

    # Throttle always 1.
    ctrl.throttle = 1

    # Handbrake if large angle.
    if abs(angle) > 1.65:
        ctrl.handbrake = True
    elif abs(angle) < 0.3:
        ctrl.boost = True

    return ctrl