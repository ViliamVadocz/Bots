"""Data Processing and Managment"""

from RLClasses  import *
from RLFunc     import *

def init(s, SCS):
    """runs initialisation"""
    s.ctrl      = SCS

    s.player         = Car(s.index)
    s.ball           = Ball()

    field_info  = s.get_field_info()

    s.l_pads    = []
    s.s_pads    = []

    for i in range(field_info.num_boosts):
        pad = field_info.boost_pads[i]
        pad_type = s.l_pads if pad.is_full_boost else s.s_pads
        pad_obj = BoostPad(i, a3v(pad.location))
        pad_type.append(pad_obj)

    s.dt            = 1 / 120.0
    s.last_time     = 0.0



def process(s, p):
    """processes gametick packet"""

    #player
    s.player.pos    = a3v(p.game_cars[s.index].physics.location)
    s.player.rot    = a3r(p.game_cars[s.index].physics.rotation)
    s.player.vel    = a3v(p.game_cars[s.index].physics.velocity)
    s.player.ang_vel= a3v(p.game_cars[s.index].physics.angular_velocity)
    s.player.on_g   = p.game_cars[s.index].has_wheel_contact
    s.player.sonic  = p.game_cars[s.index].is_super_sonic
    #s.player.orient_m = orientMat(s.player.rot)
    #s.player.turn_r  = turning_radius(np.linalg.norm(s.player.vel))

    #ball
    s.ball.pos      = a3v(p.game_ball.physics.location)
    s.ball.vel      = a3v(p.game_ball.physics.velocity)
    s.ball.ang_vel  = a3v(p.game_ball.physics.angular_velocity)
    s.ball.last_t   = p.game_ball.latest_touch.player_name

    #teammates
    s.teammates = []

    #opponents
    s.opponents = []

    #boost pads
    s.active_pads = []
    for pad_type in (s.l_pads, s.s_pads):
        for pad in pad_type:
            pad.active = p.game_boosts[pad.index].is_active
            pad.timer = p.game_boosts[pad.index].timer
            if pad.active == True:
                s.active_pads.append(pad)

    #game info
    s.time          = p.game_info.seconds_elapsed
    s.dt            = s.time - s.last_time
    s.last_time     = s.time
    s.r_active      = p.game_info.is_round_active
    s.ko_pause      = p.game_info.is_kickoff_pause