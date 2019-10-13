from rlbot.utils.rendering.rendering_manager import RenderingManager
from numpy import sign, hypot, sin, cos

def display_float( \
    r : RenderingManager, \
    value : float, \
    name : str = 'display name', \
    x : int = 20, \
    y : int = 20, \
    width : int = 200, \
    height : int = 60):
    """Draws a value in a box with coloured bars.
    
    Arguments:
        r {RenderingManager} -- Renderer.
        value {float} -- Value to display.

    Keyword Arguments:
        name {str} -- Name for the value. (default: {'display name'})
        x {int} -- X position of the box's top left corner. (default: {20})
        y {int} -- Y position of the box's top left corner. (default: {20})
        width {int} -- Width of the box. (default: {200})
        height {int} -- Height of the box. (default: {60})
    """
    # Calculations:
    pad = width / 20
    bar_width = width/2 - pad
    bar_height = 3*height/5 - 2*pad
    value_width = bar_width*abs(value)

    # Rendering:
    r.begin_rendering(f'display {name} in box')

        #Box
    colour_box = r.create_color(150, 0, 0, 0)
    r.draw_rect_2d(x, y, int(width*0.95), height, True, colour_box)
    # BUG Rects draw too wide. Temporary workaround.

        #Title
    colour_name = r.white()
    font_size = int(height / 150) + 1
    r.draw_string_2d(int(x+pad), int(y+pad), font_size, font_size, f'{name}', colour_name)

        #Bar
    pos = r.create_color(255, 0, 200, 50)
    neg = r.create_color(255, 150, 20, 20)
    colour_bar = pos if sign(value) == 1 else neg

    if sign(value) == 1:
        r.draw_rect_2d(int(x+width/2), int(y+pad + 2*height/5), int(value_width*0.95), int(bar_height), True, colour_bar)
        # BUG Rects draw too wide. Temporary workaround.
    else:
        r.draw_rect_2d(int(x+width/2-value_width), (y+pad + 2*height/5), int(value_width*0.95), int(bar_height), True, colour_bar)
        # BUG Rects draw too wide. Temporary workaround.

        #Zero Line
    colour_zero = r.white()
    r.draw_rect_2d(int(x+width/2)-1, int(y+pad + 2*height/5)-2, 2, int(bar_height)+4, True, colour_zero)

    r.end_rendering()


def display_xyfloats(r : RenderingManager, value_x : float, value_y : float, name : str = 'display name', x : int = 20, y : int = 20, size : int = 150):
    """Draws a point at the position defined by the two values, similar to a joystick.
    
    Arguments:
        r {RenderingManager} -- Renderer.
        value_x {float} -- Value to display on the x axis.
        value_y {float} -- Value to display on the y axis.
    
    Keyword Arguments:
        name {str} -- Name for the display (default: {'display name'})
        x {int} -- X position of the joysticks's top left corner. (default: {20})
        y {int} -- Y position of the joysticks's top left corner. (default: {20})
        size {int} -- Size of the joystick. (defaut: {150}) 
    """
    # Calculations:
    pad = size / 20
    axis_len = size/2 - 2*pad
    origin_x = x + size/2
    origin_y = y + size/2 + 3*pad
    
        #Circularise
    magnitude = hypot(value_x, value_y)
    greater = value_x if value_x >= value_y else value_y
    if not magnitude == 0:
        value_x *= greater/magnitude
        value_y *= greater/magnitude

    # Rendering:
    r.begin_rendering(f'display {name} as xy')

        #Box
    colour_box = r.create_color(150, 0, 0, 0)
    r.draw_rect_2d(x, y, int(size*0.95), int(size+2*pad), True, colour_box)
    # BUG Rects draw too wide. Temporary workaround.

        #Title
    colour_name = r.white()
    font_size = int(size / 300) + 1
    r.draw_string_2d(int(x+pad), int(y+pad), font_size, font_size, f'{name}', colour_name)

        #Axes
    colour_axes = r.white()
    r.draw_rect_2d(int(origin_x)-1, int(origin_y-axis_len), 3, int(axis_len*2), True, colour_axes)
    r.draw_rect_2d(int(origin_x-axis_len), int(origin_y)-1, int(axis_len*2*0.95), 3, True, colour_axes)
    # BUG Rects draw too wide. Temporary workaround.

        #Point
    colour_point = r.cyan()
    r.draw_rect_2d(int(origin_x + axis_len*value_x - pad/2), int(origin_y - axis_len*value_y - pad/2), int(pad), int(pad), True, colour_point)
    
    r.end_rendering()






