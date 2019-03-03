from RLUtilities.LinearAlgebra import vec3, norm, dot
import math

def debug(self):
    """prints debug info"""
    self.renderer.begin_rendering("debug")
    self.renderer.draw_string_2d(self.RLwindow[2]*0.75, 10, 2, 2, str(self.state), self.renderer.red())
    self.renderer.draw_string_2d(self.RLwindow[2]*0.7, 40, 1, 1, "car pos: " + str(self.info.my_car.pos), self.renderer.black())
    self.renderer.draw_string_2d(self.RLwindow[2]*0.7, 55, 1, 1, "timer: " + str(self.timer), self.renderer.black())
    self.renderer.draw_string_2d(self.RLwindow[2]*0.7, 70, 1, 1, "target speed: " + str(self.target_speed), self.renderer.black())
    if not self.target == None:
        self.renderer.draw_string_2d(self.RLwindow[2]*0.7, 85, 1, 1, "angle to target: " + str(math.atan2(dot(self.target,self.info.my_car.theta)[1], -dot(self.target,self.info.my_car.theta)[0])), self.renderer.black())
    self.renderer.end_rendering()


def target(self):
    """renders target in blue"""
    self.renderer.begin_rendering("target")
    self.renderer.draw_rect_3d(self.target, 10, 10, True, self.renderer.blue())
    self.renderer.end_rendering()


def turn_circles(self):
    """renders turning circles in cyan"""
    speed = norm(self.info.my_car.vel)
    r = -6.901E-11 * speed**4 + 2.1815E-07 * speed**3 - 5.4437E-06 * speed**2 + 0.12496671 * speed + 157
    k = self.turn_c_quality

    circleR = []
    centreR = vec3(0,r,0)
    for i in range(k):
        theta = (2/k) * math.pi * i
        point = centreR + vec3(r*math.sin(theta), -r*math.cos(theta), 0)
        point = self.info.my_car.pos + dot(self.info.my_car.theta, point)
        circleR.append(point)

    circleL = []
    centreL = vec3(0,-r,0)
    for i in range(k):
        theta = (2/k) * math.pi * i
        point = centreL + vec3(r*math.sin(theta), r*math.cos(theta), 0)
        point = self.info.my_car.pos + dot(self.info.my_car.theta, point)
        circleL.append(point)

    self.renderer.begin_rendering("turn circles")
    self.renderer.draw_polyline_3d(circleR, self.renderer.cyan())
    self.renderer.draw_polyline_3d(circleL, self.renderer.cyan())
    self.renderer.end_rendering()