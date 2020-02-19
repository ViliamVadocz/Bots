from pathlib import Path

from rlbot.agents.hivemind.drone_agent import DroneAgent

# Dummy agent to call request MyHivemind.
class DummyDroneAgent(DroneAgent):
    hive_path = str(Path(__file__).parent / 'hive.py')
    hive_key = 'TheSwarmHungers'
    hive_name = 'Overmind'