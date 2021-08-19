__author__ = "Philip Zimmermann"
__email__ = "philip.zimmermann@tum.de"
__version__ = "1.0"

try:
    from PySide import QtGui
    from PySide.QtGui import QPainter, QColor, QFont, QPen, QLabel
except ModuleNotFoundError:
    from PyQt5 import QtGui, QtCore
    from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QPushButton, QLabel
    from PyQt5.QtGui import QPainter, QColor, QFont, QPen

import facade_gui


class MyQtLabel(QLabel):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.cur_click = None
        self.cur_release = None

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.button() == 1:
            print('Press', ev.x(), ev.y(), ev.button())
            self.cur_click = (ev.x(), ev.y())

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.button() == 1 and ev.x() != self.cur_click[0] and ev.y() != self.cur_click[1]:
            print('Release', ev.x(), ev.y(), ev.button())
            self.cur_release = (ev.x(), ev.y())
            self.owner.add_rectangle(self.cur_click, self.cur_release)
            self.update()

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        super().paintEvent(a0)
        qp = QPainter()
        qp.begin(self)
        for fac_object in self.owner.facade_objects:
            if fac_object[2] == facade_gui.WINDOW:
                qp.setPen(QPen(QColor(10, 10, 255), 3))
            if fac_object[2] == facade_gui.BALCONY:
                qp.setPen(QPen(QColor(200, 200, 0), 3))

            width = abs(fac_object[0][0] - fac_object[1][0])
            height = abs(fac_object[0][1] - fac_object[1][1])
            x = min(fac_object[0][0], fac_object[1][0])
            y = min(fac_object[0][1], fac_object[1][1])
            qp.drawRect(x, y, width, height)
        qp.end()
