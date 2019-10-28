# Hivemind Example Bot

This is a custom Rocket League bot which uses one process to control multiple bots.
The example code provided showcases how hiveminds can be used for coordinated manoeuvres, such as team pinches (A special move where the ball is squeezed between two cars to launch it at high speeds.)

[A GIF of this example bot in action](https://gfycat.com/exemplaryeminentflyingfish-rocketleague)

## Overview of the Structure

The *hivemind* is just a single process controlling multiple bots.

The general structure is composed of a bot file that creates a `helper process request` and a main *hivemind* file.
The bot file initiates a separate process which then receives all of the bot indices which requested it with the same key, which the process can then use to send control inputs to the bots.

Below is the bot file `hive_example.py`. This is the file you point your config towards. (i.e. `python_file = ./hive_example.py`)
The code inside will be very similar in every hivemind bot, except for the **keys**. It is important that your **keys are unique**, because otherwise the first process with those keys will initiate a hivemind that will then also control your bots (with the same key). It is also important to have **different keys for the Blue and Orange teams**, otherwise only a single hivemind process will be initiated for both teams.

```python
'''
Main bot file, just requests the hivemind helper process.
Your hivemind code goes in hivemind.py.
'''

import os

from rlbot.agents.base_independent_agent import BaseIndependentAgent
from rlbot.botmanager.helper_process_request import HelperProcessRequest

class HiveBot(BaseIndependentAgent):

    def __init__(self, name, team, index):
        super().__init__(name, team, index)

    def get_helper_process_request(self) -> HelperProcessRequest:
        """Requests a helper process"""

        # File path to the hivemind file. If you rename it, also rename it here.
        file_path = os.path.join(os.path.dirname(__file__), 'hivemind.py')

        # Differentiates between teams so each team has its own hivemind.
        # Make sure to make your keys something unique, otherwise other people's hiveminds could take over.
        key = 'Blue Example Hivemind' if self.team == 0 else 'Orange Example Hivemind'

        # Creates request for helper process.
        request = HelperProcessRequest(file_path, key, options={})

        return request

    def run_independently(self, terminate_request_event):
        pass
```

## The Hivemind

This is the main *hivemind* file. This includes the `bot helper process` that is requested by the bots. You will most likely only be modifying the `start()` and `game_loop()` functions.

In `__init__()`, a logger is created that you can use to print info into the console. More notably, a **GameInterface** is created which you will use to access things such as the GameTickPacket, BallPrediction, or FieldInfo. `self.running_indices` is also initialised, which will contain the indices of the bots that request this process.

In `start()`, The process fetches the agent indices. If you are trying to run a lot of bots and running into problems where they cannot join to the *hivemind*, try increasing the amount of time that you sleep for before running `try_receive_agent_metadata()`.
You can put initialisation code here if you want, such as creating objects for *drones* (Shown later).

Now we get to `game_loop()`. This is where your *hivemind* will spend the rest of it's time. It contains an infinite loop. Each time it loops, it checks whether a new packet from the game has arrived. If it did, it runs your code. You can think of this loop running every game tick, similar to how normal python bots get their `get_output()` called every tick.

To send the control input to each bot under the *hivemind's* control, you create a `PlayerInput` object which is very similar to the more familiar `SimpleControllerState`. You then use `self.game_interface.update_player_input()` to send the controls to each bot index.

The code below is very bare-bones. Bots will just sit there, doing nothing.

```python
'''The Hivemind'''

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

        # Runs the game loop where the hivemind will spend the rest of its time.
        self.game_loop()


    def game_loop(self):
        """The main game loop. This is where your hivemind code goes."""

        packet = GameTickPacket()

        # MAIN LOOP:
        while True:

            previous_packet_time = packet.game_info.seconds_elapsed

            # Updating the game packet from the game.
            self.game_interface.update_live_data_packet(packet)

            # Checking if packet is old. If yes, sleep and skip running the code.
            if previous_packet_time == packet.game_info.seconds_elapsed:
                time.sleep(0.001)
                continue

            # YOUR CODE STARTS HERE:
            controller_state = PlayerInput() # Almost identical to SimpleControllerState.

            for index in self.running_indices:
                # Use this to send controllers to each bot.
                self.game_interface.update_player_input(controller_state, index)
```

## Doing Something More Complex

No doubt, you are not satisfied with a bot that does nothing. I bet you already have ideas brewing for what to try. That's great!

To get more complex behaviour out of your *hivemind*, it is very useful to know more about your *drones*, the bots which you control.

This is why I make a `Drone` class which holds information about the *drone*. The one below has been stripped, so it only includes the parts necessary for my example. In a real bot it would additionally house things like its position, velocity, rotation, and other attributes.

(You could also use `dataclasses` for this if you are familiar with them.)

```python
class Drone:
    """Houses the processed data from the packet for the drones.

    Attributes:
        index {int} -- The car's index in the packet.
        team {int} -- 0 if blue, else 1.
        ctrl {PlayerInput} -- The controls we want to send to the drone.
    """
    __slots__ = [
        'index',
        'team',
        'ctrl'
    ]

    def __init__(self, index: int, team: int):
        self.index: int = index
        self.team: int = team
        self.ctrl: PlayerInput = PlayerInput()
```

What I then do is create a Drone object for each of the indices found in `running_indices` and add them to a list `self.drones`. You could similarly add your opponents and team-mates to lists.

We now have a list of our *drones* and can therefore loop over it to do something for each of the bots which we control (such as send them inputs.)

The revised `ExampleHivemind` below shows how to do this.

```python
class ExampleHivemind(BotHelperProcess):

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

        ############
        # NEW CODE #
        ############

        # Create and update the packet.
        packet = GameTickPacket()
        self.game_interface.update_live_data_packet(packet)

        # Create a Drone object for every drone that holds its information.
        self.drones = []
        for index in range(packet.num_cars):
            if index in self.running_indices:
                self.drones.append(Drone(index, packet.game_cars[index].team))
            else:
                # You could add code here to add other bots to your team-mates or opponents lists.
                pass

        #############
        # /NEW CODE #
        #############

        # Runs the game loop where the hivemind will spend the rest of its time.
        self.game_loop()


    def game_loop(self):
        """The main game loop. This is where your hivemind code goes."""

        packet = GameTickPacket()

        # MAIN LOOP:
        while True:

            previous_packet_time = packet.game_info.seconds_elapsed

            # Updating the game packet from the game.
            self.game_interface.update_live_data_packet(packet)

            # Checking if packet is old. If yes, sleep and skip running the code.
            if previous_packet_time == packet.game_info.seconds_elapsed:
                time.sleep(0.001)
                continue

            # YOUR CODE STARTS HERE:

            ############
            # NEW CODE #
            ############

            for drone in self.drones:
                self.ctrl = PlayerInput() # Almost identical to SimpleControllerState.

            for drone in self.drones:
                # Use this to send controllers to each bot.
                self.game_interface.update_player_input(drone.ctrl, drone.index)

            #############
            # /NEW CODE #
            #############
```

## It Still Does Nothing?

Well, yes.

But don't worry! That's just because I didn't want to clutter this document. If you check out the actual code provided, you will find out that it includes a *hivemind* bot which attempt team pinches! How cool is that?

It is still very simple, so maybe take it as a challenge to improve it! There are plenty of comments to help guide you, and if you don't want to read through the code, you can just play around with the parameters at the top of the main file and see what happens.

If you have any unanswered questions, direct them at me either through [mail](viliam.vadocz@gmail.com) or on [discord](@Calculated_Will#4544)
