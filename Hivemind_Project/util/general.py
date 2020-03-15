def team_sign(team: int):
    return -2 * team + 1

def clamp(value, minimum, maximum):
    return max(min(value, maximum), minimum)