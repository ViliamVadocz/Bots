from typing import List

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.quick_chats import QuickChats

from util.aerial import AerialStep, LineUpForAerialStep
from util.drive import steer_toward_target
from util.goal_detector import find_future_goal
from util.sequence import Sequence, ControlStep
from util.spikes import SpikeWatcher
from util.vec import Vec3

from states import BaseState, Simple, Kickoff, WallThing, GetBoost
from numpy import random
class MyBot(BaseAgent):

    def initialize_agent(self):
        # This runs once before the bot starts up
        self.controller_state = SimpleControllerState()
        self.active_sequence: Sequence = None
        self.spike_watcher = SpikeWatcher()

        self.state = BaseState()
        self.big_pads = None

    def check_states(self, packet):
        draw_debug(self.renderer, [str(self.state)])

        if not self.state.active:
            # if Kickoff.available(self, packet):
                # self.state = Kickoff
            if WallThing.available(self, packet):
                self.state = WallThing()
            # elif GetBoost.available(self, packet):
                # self.state = GetBoost()
            elif Simple.available(self, packet):
                self.state = Simple()

        return self.state.execute(self, packet)

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        """
        This function will be called by the framework many times per second. This is where you can
        see the motion of the ball, etc. and return controls to drive your car.
        """
        if self.big_pads is None:
            # Constant values can be found the the FieldInfo:
            info = self.get_field_info()
            
            # Manually construct a list of all big boost pads
            # info.boost_pads has a fixed size but info.num_boosts is how many pads there actually are
            self.big_pads = []
            for i in range(info.num_boosts):
                pad = info.boost_pads[i]
                if pad.is_full_boost:
                    self.big_pads.append((i, pad))
        
        self.active_pads = []
        for i, pad in self.big_pads:
            if packet.game_boosts[i].is_active:
                self.active_pads.append(pad)


        self.spike_watcher.read_packet(packet)
        ball_prediction = self.get_ball_prediction_struct()

        # Example of predicting a goal event
        predicted_goal = find_future_goal(ball_prediction)
        goal_text = "RIGGED"
        if predicted_goal:
            goal_text = f"Goal in {predicted_goal.time - packet.game_info.seconds_elapsed:.2f}s"

        self.renderer.begin_rendering("<3")
        size = int(30 + 5*random.rand())
        self.renderer.draw_string_2d(400, 100, size, size, "<3", self.renderer.pink())
        self.renderer.end_rendering()

        # This is good to keep at the beginning of get_output. It will allow you to continue
        # any sequences that you may have started during a previous call to get_output.
        if self.active_sequence and not self.active_sequence.done:
            return self.active_sequence.tick(packet)

        ctrl = self.check_states(packet)

        return ctrl

    def start_aerial(self, target: Vec3, arrival_time: float):
        self.active_sequence = Sequence([
            LineUpForAerialStep(target, arrival_time, self.index),
            AerialStep(target, arrival_time, self.index)])


def draw_debug(renderer, text_lines: List[str]):
    """
    This will draw the lines of text in the upper left corner.
    This function will automatically put appropriate spacing between each line
    so they don't overlap.
    """
    renderer.begin_rendering()
    y = 350
    for line in text_lines:
        renderer.draw_string_2d(50, y, 1, 1, line, renderer.yellow())
        y += 20
    renderer.end_rendering()
