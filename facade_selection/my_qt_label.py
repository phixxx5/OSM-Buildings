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

from facade_selection.utils import Point, FacObjTypes


class MyQtLabel(QLabel):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.cur_click = None
        self.cur_release = None
        self.draw_mode = False

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.button() == 1:
            print('Press', ev.x(), ev.y(), ev.button())
            self.cur_click = Point(ev.x() / self.width(), ev.y() / self.height())
            self.draw_mode = True

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.button() == 1 and ev.x() != self.cur_click[0] and ev.y() != self.cur_click.y:
            print('Release', ev.x(), ev.y(), ev.button())
            self.cur_release = Point(ev.x() / self.width(), ev.y() / self.height())
            self.draw_mode = False
            self.update()
            self.owner.add_rectangle(self.cur_click, self.cur_release)

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        if self.draw_mode:
            self.tmp_rect = (self.cur_click.x, self.cur_click.y, ev.x() / self.width(), ev.y() / self.height())
            self.update()

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        super().paintEvent(a0)
        qp = QPainter()
        qp.begin(self)
        for fac_object in self.owner.facade_objects:
            if fac_object.type == FacObjTypes.WINDOW:
                qp.setPen(QPen(QColor(0, 205, 255), 3))
            if fac_object.type == FacObjTypes.BALCONY:
                qp.setPen(QPen(QColor(200, 200, 0), 3))
            qp.drawRect(
                *self.calculate_drawable_rect(fac_object.p1.x, fac_object.p1.y, fac_object.p2.x, fac_object.p2.y))
            qp.drawText(min(fac_object.p1.x, fac_object.p2.x) * self.width(),
                        max(fac_object.p1.y, fac_object.p2.y) * self.height() + 15,
                        'window' if fac_object.type == FacObjTypes.WINDOW else 'balcony')
        if self.draw_mode:
            qp.setPen(QPen(QColor(255, 255, 255), 3))
            qp.drawRect(
                *self.calculate_drawable_rect(self.tmp_rect[0], self.tmp_rect[1], self.tmp_rect[2], self.tmp_rect[3]))
        qp.end()

    def calculate_drawable_rect(self, x1, y1, x2, y2):
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        x = min(x1, x2)
        y = min(y1, y2)
        return x * self.width(), y * self.height(), width * self.width(), height * self.height()
