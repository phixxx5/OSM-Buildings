__author__ = "Philip Zimmermann"
__email__ = "philip.zimmermann@tum.de"
__version__ = "1.0"

try:
    from PySide import QtGui, QtCore
    from PySide.QtGui import QWidget, QApplication, QGridLayout, QPushButton, QPixmap
except ModuleNotFoundError:
    from PyQt5 import QtGui, QtCore
    from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QPushButton
    from PyQt5.QtGui import QPixmap
import my_qt_label
from collections import namedtuple

Point = namedtuple('Point', 'x y')
FacadeObject = namedtuple('FacadeObject', 'p1 p2 type')
WINDOW = 0
BALCONY = 1


class FacadeGui(QWidget):
    def __init__(self, owner, img_path):
        super().__init__()
        self.owner = owner

        self.facade_objects = []
        self.deleted_objects = []
        self.mode = WINDOW

        main_layout = QGridLayout()
        self.setFixedSize(1200, 800)

        self.window_button = QPushButton('Window')
        self.window_button.clicked.connect(self.window_call)
        self.window_button.setCheckable(True)
        self.window_button.setChecked(True)

        self.balcony_button = QPushButton('Balcony')
        self.balcony_button.clicked.connect(self.balcony_call)
        self.balcony_button.setCheckable(True)
        self.balcony_button.setChecked(False)

        finish_button = QPushButton('Finish')
        finish_button.clicked.connect(self.finish_call)

        q_image = QtGui.QImage(img_path)  # .scaled(1200, 800,aspectRatioMode=QtCore.Qt.KeepAspectRatio)
        self.image_label = my_qt_label.MyQtLabel(self)
        self.image_label.setPixmap(QPixmap.fromImage(q_image))
        self.image_label.setScaledContents(True)

        main_layout.addWidget(self.window_button, 0, 0)
        main_layout.addWidget(self.balcony_button, 0, 1)
        main_layout.addWidget(self.image_label, 1, 0, 1, 3)
        main_layout.addWidget(finish_button, 2, 1)

        self.setLayout(main_layout)
        self.show()

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        if a0.key() == 85:
            print('Undo')
            self.undo_call()
        if a0.key() == 82:
            print('Redo')
            self.redo_call()

    def add_rectangle(self, point1, point2):
        self.facade_objects.append(FacadeObject(point1, point2, self.mode))

    def window_call(self):
        print('Window')
        self.balcony_button.setChecked(False)
        self.window_button.setChecked(True)
        self.mode = WINDOW

    def balcony_call(self):
        print('Balcony')
        self.window_button.setChecked(False)
        self.balcony_button.setChecked(True)
        self.mode = BALCONY

    def finish_call(self):
        print("Finish")
        print(self.facade_objects)
        self.close()
        self.owner.insertIntoCAD(self.facade_objects)

    def undo_call(self):
        if len(self.facade_objects) > 0:
            self.deleted_objects.append(self.facade_objects.pop())
            self.image_label.update()

    def redo_call(self):
        if len(self.deleted_objects) > 0:
            self.facade_objects.append(self.deleted_objects.pop())
            self.image_label.update()


if __name__ == '__main__':
    app = QApplication([])
    FacadeGui(None, "/home/philip/workspace/baurobotik/flatten_facades/dev/Baurobotik/TUM.jpg")
    app.exec()
