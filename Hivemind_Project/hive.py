from typing import Dict

from rlbot.utils.structures.bot_input_struct import PlayerInput
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.agents.hivemind.drone_agent import DroneAgent
from rlbot.agents.hivemind.python_hivemind import PythonHivemind

# Dummy agent to call request MyHivemind.
class Drone(DroneAgent):
    hive_path = __file__
    hive_key = 'ChangeThisKey'
    hive_name = 'Example Hivemind'
    

class MyHivemind(PythonHivemind):

    def initialize_hive(self, packet: GameTickPacket) -> None:
        self.logger.info('Initialised!')

        # Find out team by looking at packet.
        # drone_indices is a set, so you cannot just pick first element.
        index = next(iter(self.drone_indices))
        self.team = packet.game_cars[index].team

    def get_outputs(self, packet: GameTickPacket) -> Dict[int, PlayerInput]:

        return {index: PlayerInput() for index in self.drone_indices}