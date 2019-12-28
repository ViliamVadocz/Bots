'''The Hivemind'''
# This is a clean version of hivemind.py so it is easier to start your hivemind bot.

import queue
import time

from rlbot.botmanager.agent_metadata import AgentMetadata
from rlbot.botmanager.bot_helper_process import BotHelperProcess
from rlbot.utils.logging_utils import get_logger
from rlbot.utils.structures.bot_input_struct import PlayerInput
from rlbot.utils.structures.game_data_struct import GameTickPacket, FieldInfoPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction
from rlbot.utils.structures.game_interface import GameInterface

class ExampleHivemind(BotHelperProcess):

    # Some terminology:
    # hivemind = the process which controls the drones.
    # drone = a bot under the hivemind's control.

    def __init__(self, agent_metadata_queue, quit_event, options):
        super().__init__(agent_metadata_queue, quit_event, options)

        # Sets up the logger. The string is the name of your hivemind.
        # Call this something unique so people can differentiate between hiveminds.
        self.logger = get_logger('Example Hivemind')

        # The game interface is how you get access to things
        # like ball prediction, the game tick packet, or rendering.
        self.game_interface = GameInterface(self.logger)

        # running_indices is a set of bot indices
        # which requested this hivemind with the same key.
        self.running_indices = set()


    def try_receive_agent_metadata(self):
        """Adds all drones with the correct key to our set of running indices."""
        while True:  # Will exit on queue.Empty
            try:
                # Adds drone indices to running_indices set.
                single_agent_metadata: AgentMetadata = self.metadata_queue.get(
                    timeout=0.1)
                self.running_indices.add(single_agent_metadata.index)

            except queue.Empty:
                return

            except Exception as ex:
                self.logger.error(ex)


    def start(self):
        """Runs once, sets up the hivemind and its agents."""
        # Prints an activation message into the console.
        # This lets you know that the process is up and running.
        self.logger.info("Hello World!")

        # Loads game interface.
        self.game_interface.load_interface()

        # Wait a moment for all agents to have a chance to start up and send metadata.
        self.logger.info("Snoozing for 3 seconds; give me a moment.")
        # Increase this number if you're having issues
        # with bots not being added to the hivemind.
        time.sleep(3)
        self.try_receive_agent_metadata()

        self.logger.info("Finished sleeping. Ready to go!")

        # This is how you access field info.
        # First create the initialise the object...
        field_info = FieldInfoPacket()
        # Then update it.
        self.game_interface.update_field_info_packet(field_info)

        # Same goes for the packet, but that is
        # also updated in the main loop every tick.
        packet = GameTickPacket()
        self.game_interface.update_live_data_packet(packet)
        # Ball prediction works the same. Check the main loop.

        # Create a Ball object for the ball that holds its information.
        self.ball = Ball()

        # Create a Drone object for every drone that holds its information.
        self.drones = []
        for index in range(packet.num_cars):
            if index in self.running_indices:
                self.drones.append(Drone(index))

        # Runs the game loop where the hivemind will spend the rest of its time.
        self.game_loop()


    def game_loop(self):
        """The main game loop. This is where your hivemind code goes."""

        # Creating packet and ball prediction objects which will be updated every tick.
        packet = GameTickPacket()
        ball_prediction = BallPrediction()

        # Nicknames the renderer to shorten code.
        draw = self.game_interface.renderer

        # MAIN LOOP:
        while True:

            previous_packet_time = packet.game_info.seconds_elapsed

            # Updating the game packet from the game.
            self.game_interface.update_live_data_packet(packet)

            # Checking if packet is old. If yes, sleep and skip running the code.
            if previous_packet_time == packet.game_info.seconds_elapsed:
                time.sleep(0.001)
                continue

            for drone in self.drones:
                self.ctrl = PlayerInput()

            # YOUR CODE GOES HERE:
            print('Hivemind is running')

            # Use this to send the drone inputs to the drones.
            for drone in self.drones:
                self.game_interface.update_player_input(
                    drone.ctrl, drone.index)


# Clean drone class.
class Drone:
    def __init__(self, index: int):
        self.index: int = index
        self.ctrl: PlayerInput = PlayerInput()
