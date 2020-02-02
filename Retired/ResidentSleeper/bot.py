# library imports.
import numpy as np

# RLBot imports.
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.quick_chats import QuickChats

# RLU imports.
# from RLUtilities

# Local file imports.
import data
from states import Idle, Kickoff, SimplePush, Demo, GetBoost


class ResidentSleeper(BaseAgent):

    def initialize_agent(self):
        self.need_setup = True
        self.state = Idle()


    def checkState(self):
        # Trigger kickoff state whenever available.
        if not isinstance(self.state, Kickoff) and Kickoff.available(self): self.state = Kickoff()

        if self.state.expired:
            if Kickoff.available(self):
                self.state = Kickoff()
            elif GetBoost.available(self):
                self.state = GetBoost()
            elif Demo.available(self):
                self.state = Demo()
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
            self.state.execute(self)

        # print(
        # """
        # ##     ##   ######
        # ##     ##     ##
        # ##     ##     ##
        # #########     ##
        # ##     ##     ##
        # ##     ##     ##
        # ##     ##   ######
        # """)

        self.renderer.begin_rendering('HI')
        self.renderer.draw_string_2d(200, 700, 4, 4, 'Sad noises :(', self.renderer.black())
        self.renderer.end_rendering()

        return self.ctrl