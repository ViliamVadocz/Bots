import keyboard
import sys
import time

from importlib import import_module
from queue import Queue
from threading import Thread

from rlbot.setup_manager import SetupManager
from rlbot.utils.game_state_util import GameState
from rlbot.utils.logging_utils import get_logger
from rlbot.utils.python_version_check import check_python_version
from rlbot.utils.structures.game_interface import GameInterface


class Message:
    READY = 0
    DONE = 1


TESTS = {
    "single_bot": ["ceiling_recovery1", "ceiling_recovery2"],
    # "three_bots": ["kickoff"],
}


RESET_KEY = "r"
NEXT_KEY = "p"

# TODO
# Send some description of the test to render.


def run_state_setting(my_queue: Queue):
    """Controls state setting for tests."""
    message = my_queue.get()
    if message != Message.READY:
        raise Exception(f"Got {message} instead of READY")

    logger = get_logger("UTSS")  # Unit Test State Setting
    game_interface = GameInterface(logger)
    game_interface.load_interface()
    game_interface.wait_until_loaded()
    logger.info("Running!")

    # Get the first GameState.
    game_state, message = my_queue.get()
    game_interface.set_game_state(game_state)

    while True:
        while my_queue.qsize() == 0:
            # Sleep to prevent reset-spamming.
            time.sleep(0.1)

            if not keyboard.is_pressed(RESET_KEY):
                continue

            # Reset the GameState.
            logger.info("Resetting test.")
            game_interface.set_game_state(game_state)

        # Receive GameState.
        logger.info("Setting new test.")
        game_state, message = my_queue.get()
        if message == Message.DONE:
            print('Thread 2 closing.')
            exit()

        game_interface.set_game_state(game_state)


def get_game_state(module_path):
    import_module(module_path)
    module = sys.modules[module_path]
    if isinstance(module.GAME_STATE, GameState):
        return module.GAME_STATE
    else:
        raise Exception("GAME_STATE is not an instance of GameState.")


def run_tests(my_queue: Queue):
    """Runs the tests."""
    check_python_version()
    manager = SetupManager()

    has_started = False

    for config in TESTS:
        if len(TESTS[config]) == 0:
            continue

        # Start a match.
        config_location = f"./tests/{config}/rlbot.cfg"
        manager.load_config(config_location=config_location)
        manager.connect_to_game()
        manager.launch_early_start_bot_processes()
        manager.start_match()
        manager.launch_bot_processes()

        if not has_started:
            # Let other thread know that game has been launched.
            my_queue.put(Message.READY)
            has_started = True

        # Load first test for this config.
        test_num = 0
        my_queue.put(
            (get_game_state(f"tests.{config}.{TESTS[config][test_num]}"), None)
        )

        while not manager.quit_event.is_set():
            manager.try_recieve_agent_metadata()

            # Move onto the next test.
            if keyboard.is_pressed(NEXT_KEY):
                test_num += 1

                # If we have exceeded the number of tests in this config,
                # break and go to the next config.
                if len(TESTS[config]) <= test_num:
                    break

                # Loads the next test.
                my_queue.put(
                    (get_game_state(f"tests.{config}.{TESTS[config][test_num]}"), None)
                )

                # Prevent accidental multiple key presses.
                time.sleep(1)

        # Kills the previous hivemind / other bots.
        manager.shut_down(kill_all_pids=True)

    my_queue.put((None, Message.DONE))
    print("Thread 1 closing.")
    exit()


if __name__ == "__main__":

    q = Queue()
    thread1 = Thread(target=run_tests, args=(q, ))
    thread1.start()
    thread2 = Thread(target=run_state_setting, args=(q, ))
    thread2.start()
    q.join()
