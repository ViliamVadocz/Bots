from rlbot.utils.structures.bot_input_struct import PlayerInput

def team_sign(team: int):
    return -2 * team + 1

def clamp(value, minimum, maximum):
    return max(min(value, maximum), minimum)

def to_player_input(controls) -> PlayerInput:
    """Convert controls to PlayerInput"""
    player_input = PlayerInput()
    player_input.throttle = controls.throttle
    player_input.steer = controls.steer
    player_input.pitch = controls.pitch
    player_input.yaw = controls.yaw
    player_input.roll = controls.roll
    player_input.jump = controls.jump
    player_input.boost = controls.boost
    player_input.handbrake = controls.handbrake
    # RLUtilities Input does not have a use_item attribute.
    if hasattr(controls, "use_item"):
        player_input.use_item = controls.use_item

    return player_input