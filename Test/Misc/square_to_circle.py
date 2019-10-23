from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QCheckBox, QGridLayout, \
    QGroupBox, QMenu, QPushButton, QRadioButton, QVBoxLayout, QWidget, QSlider
from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5.QtCore import Qt
import sys

import numpy as np
PI = np.pi

def map_square_to_circle (x, y):
    """Maps the points in a square to the points 
    of a circle / disc. The points will have the 
    same angle and the ratio of distance from 
    origin to maximum distance will be conserved.
    
    Arguments:
        x {float} -- x coordinate of point inside the square.
        y {float} -- y coordinate of point inside the square.
    
    Returns:
        new_x {float} -- x coordinate of point inside the circle.
        new_y {float} -- y coordinate of point inside the circle.
    """

    def rep_of_max (angle : float) -> float:
        """Uses the appropriate function based on angle.
        Functions will be the reciprocal of the of length 
        from the origin to the sides of a square centered 
        on the origin with side length two.
        
        Arguments:
            angle {float} -- angle measured in radians.
        
        Returns:
            float -- Reciprocal of the length.
        """
        # Make angle positive.
        if angle < 0: angle += 2*PI

        # Find correct function based on angle.
        if 3*PI/4 >= angle > PI/4:
            return np.sin(angle)
        elif 5*PI/4 >= angle > 3*PI/4:
            return -np.cos(angle)
        elif 7*PI/4 >= angle > 5*PI/4:
            return -np.sin(angle)
        else:
            return np.cos(angle)

    # Calculates the angle and scale factor.
    angle = np.arctan2(y, x)
    scale = rep_of_max(angle) * np.hypot(x, y)
    
    # Makes a new point in the circle.
    new_x, new_y = scale * np.cos(angle), scale * np.sin(angle)
    return new_x, new_y
    

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Square to Circle")
        self.setGeometry(400, 200, 1000, 500)
        
        self.slider_x = QSlider(Qt.Horizontal, self)
        self.slider_x.setFocusPolicy(Qt.StrongFocus)
        self.slider_x.setTickPosition(QSlider.TicksBothSides)
        self.slider_x.setTickInterval(10)
        self.slider_x.setSingleStep(1)
        self.slider_x.resize(400,20)
        self.slider_x.move(50,25)
        self.slider_x.setValue(0)
        self.slider_x.valueChanged.connect(self.update)

        self.slider_y = QSlider(Qt.Vertical, self)
        self.slider_y.setFocusPolicy(Qt.StrongFocus)
        self.slider_y.setTickPosition(QSlider.TicksBothSides)
        self.slider_y.setTickInterval(10)
        self.slider_y.setSingleStep(1)
        self.slider_y.resize(20,400)
        self.slider_y.move(25,50)
        self.slider_y.setValue(0)
        self.slider_y.valueChanged.connect(self.update)
    
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw axes.
        painter.setPen(QPen(Qt.black,  1, Qt.SolidLine))
        painter.drawLine(250, 50, 250, 450)
        painter.drawLine(50, 250, 450, 250)
        painter.drawLine(750, 50, 750, 450)
        painter.drawLine(550, 250, 950, 250)

        # Draw square and circle.
        painter.setPen(QPen(Qt.blue,  1, Qt.SolidLine))
        painter.drawRect(50, 50, 400, 400)
        painter.drawEllipse(550, 50, 400, 400)

        # Draw points.
        x = (self.slider_x.value() - 49.5)/49.5
        y = -(self.slider_y.value() - 49.5)/49.5

        painter.setPen(QPen(Qt.blue,  1, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.blue, Qt.SolidPattern))
        painter.drawEllipse(245 + x*200, 245 + y*200, 10, 10)

        new_x, new_y = map_square_to_circle(x, y)
        print(x, y, new_x, new_y)

        painter.setPen(QPen(Qt.blue,  1, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.blue, Qt.SolidPattern))
        painter.drawEllipse(745 + new_x*200, 245 + new_y*200, 10, 10)


if __name__ == "__main__":
    App = QApplication(sys.argv)
    window = Window()
    sys.exit(App.exec())