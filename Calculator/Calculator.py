'''Main bot file.'''

# RLBot imports.
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.quick_chats import QuickChats

# Local file imports.
import data
from utils import np, a3l, normalise, local, cap, team_sign, special_sauce
from states import Idle, Kickoff, Catch, PickUp, Dribble, SimplePush, GetBoost, Dodge, orange_inside_goal

class Calculator(BaseAgent):

    def initialize_agent(self):
        self.need_setup = True
        self.state = Idle()

        # Fake kickoff related.
        self.fake_kickoff_works = False
        self.went_for_fake_ko = -1
        self.enemy_goals = 0

        # Restraint to prevent Calculated spam.
        self.restraint = 0


    def checkState(self):
        
        # TODO Check if near active pad, take it

        # Trigger kickoff state whenever available.
        if not isinstance(self.state, Kickoff) and Kickoff.available(self): self.state = Kickoff()

        if self.state.expired:
            if Kickoff.available(self):
                self.state = Kickoff()
            elif Dribble.available(self):
                self.state = Dribble()
            elif PickUp.available(self):
                self.state = PickUp()
            elif Catch.available(self):
                self.state = Catch()
            elif GetBoost.available(self):
                self.state = GetBoost()
            else:
                self.state = SimplePush()


    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        # Runs setup.
        if self.need_setup:
            field_info = self.get_field_info()
            data.setup(self, packet, field_info)
            self.need_setup = False

        # Preprocessing.
        data.process(self, packet)
        self.ctrl = SimpleControllerState()

        # Handle states.
        self.checkState()

        # Execute state.
        if not self.state.expired:
            # Don't do anything if about to score.
            if len(self.opponents) == 1:
                opponent_goal = orange_inside_goal * team_sign(self.team)

                my_dist_to_goal = np.linalg.norm(self.player.pos - opponent_goal)
                opp_dist_to_goal = np.linalg.norm(self.opponents[0].pos - opponent_goal)
                opp_closer_to_goal = my_dist_to_goal > opp_dist_to_goal

                if self.team == 0:
                    in_goal_predictions = self.ball.predict.pos[:,1][:120] > 5150
                    # opponent_behind = self.opponents[0].pos[1] > self.ball.pos[1]
                else:
                    in_goal_predictions = self.ball.predict.pos[:,1][:120] < -5150
                    # opponent_behind = self.opponents[0].pos[1] < self.ball.pos[1]

                about_to_score = np.count_nonzero(in_goal_predictions) > 60 and not opp_closer_to_goal

                if not about_to_score:
                    self.state.execute(self)
                    # TODO self.state.render(self)
                else:
                    if self.restraint == 0:
                        self.send_quick_chat(QuickChats.CHAT_EVERYONE, QuickChats.Reactions_Calculated)
                        self.restraint = 360
                    else:
                        self.restraint -= 1

            else:
                self.state.execute(self)
            
        # If got scored on less than 20 seconds after a fake kickoff, don't do it again.
        if packet.teams[abs(self.team - 1)].score > self.enemy_goals:
            if self.went_for_fake_ko != -1 and self.game_time - self.went_for_fake_ko < 20.0:
                self.fake_kickoff_works = False
        self.enemy_goals = packet.teams[abs(self.team - 1)].score

        # Render.
        self.render(self.renderer)

        return self.ctrl 


    def render(self, r):
        r.begin_rendering()
        r.draw_string_2d(150, 10, 2, 2, f'{self.state.__class__.__name__}', r.white())
        r.draw_polyline_3d(self.ball.predict.pos[:120:10], r.pink())
        r.end_rendering()