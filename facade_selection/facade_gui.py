__author__ = "Philip Zimmermann"
__email__ = "philip.zimmermann@tum.de"
__version__ = "1.0"

from typing import List

from facade_selection.utils import FacObjTypes, Point

try:
    from PySide import QtGui, QtCore
    from PySide.QtGui import QWidget, QApplication, QGridLayout, QPushButton, QPixmap, QComboBox, QLabel, QCheckBox
except ModuleNotFoundError:
    from PyQt5 import QtGui, QtCore
    from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QPushButton, QComboBox, QLabel, QCheckBox
    from PyQt5.QtGui import QPixmap

import facade_selection.my_qt_label
import facade_selection.grid_dialog
from facade_selection.facade_object import FacadeObject


class FacadeGui(QWidget):
    def __init__(self, owner, img_path: str):
        super().__init__()
        self.owner = owner

        self.facade_objects: List[FacadeObject] = []
        self.deleted_objects: List[FacadeObject] = []
        self.mode: FacObjTypes = FacObjTypes.WINDOW
        self.grid_mode: bool = False
        self.grid_placed: int = 0

        main_layout = QGridLayout()
        self.setFixedSize(1200, 800)

        self.mode_combo_box = QComboBox()
        self.mode_combo_box.addItems(['Window', 'Balcony'])
        self.mode_combo_box.currentTextChanged.connect(self.mode_change_call)

        self.grid_box = QCheckBox('Grid mode')
        self.grid_box.clicked.connect(self.grid_call)

        self.standard_text = 'Left-click and move mouse to mark facade objects. Press \'Finish\' when ready to continue.'
        self.grid_mode_text = 'Grid Mode: Mark only the top-left and bottom-right facade objects in the grid.'
        self.status_label = QLabel(self.standard_text)

        undo_button = QPushButton('Undo')
        undo_button.clicked.connect(self.undo_call)
        redo_button = QPushButton('Redo')
        redo_button.clicked.connect(self.redo_call)
        finish_button = QPushButton('Finish')
        finish_button.clicked.connect(self.finish_call)

        q_image = QtGui.QImage(img_path)  # .scaled(1200, 800,aspectRatioMode=QtCore.Qt.KeepAspectRatio)
        self.image_label = facade_selection.my_qt_label.MyQtLabel(self)
        self.image_label.setPixmap(QPixmap.fromImage(q_image))
        self.image_label.setScaledContents(True)

        main_layout.addWidget(self.status_label, 0, 0, 1, -1)
        main_layout.addWidget(self.grid_box, 1, 0)
        main_layout.addWidget(self.mode_combo_box, 2, 0)
        main_layout.addWidget(undo_button, 2, 1)
        main_layout.addWidget(redo_button, 2, 2)
        main_layout.addWidget(finish_button, 2, 3)
        main_layout.addWidget(self.image_label, 3, 0, 1, -1)

        self.setLayout(main_layout)
        self.show()

    def add_rectangle(self, point1, point2):
        self.facade_objects.append(FacadeObject(point1, point2, self.mode))
        if self.grid_mode:
            self.grid_placed += 1
            if self.grid_placed == 2:
                self.open_grid_menu()

    def open_grid_menu(self):
        assert len(self.facade_objects) >= 2
        grid_dialog = facade_selection.grid_dialog.GridDialog(self)
        grid_dialog.exec()

    def autocomplete_grid(self, rows, columns):
        fac_obj_1, fac_obj_2 = self.facade_objects[-2:]
        assert fac_obj_1.p1.x < fac_obj_2.p2.x
        avg_width = (fac_obj_1.width() + fac_obj_2.width()) / 2
        avg_height = (fac_obj_1.height() + fac_obj_2.height()) / 2
        fac_obj_1.set_width(avg_width)
        fac_obj_1.set_height(avg_height)
        fac_obj_2.set_width(avg_width)
        fac_obj_2.set_height(avg_height)
        # calculate intermediate spaces size
        x_spaces = (abs(fac_obj_2.p2.x - fac_obj_1.p1.x) - columns * avg_width) / (columns - 1) if columns > 1 else 0
        y_spaces = (abs(fac_obj_2.p2.y - fac_obj_1.p1.y) - rows * avg_height) / (rows - 1) if rows > 1 else 0
        self.facade_objects.pop()
        self.facade_objects.pop()
        for row in range(rows):
            for column in range(columns):
                p1 = Point(fac_obj_1.p1.x + column * (avg_width + x_spaces),
                           fac_obj_1.p1.y + row * (avg_height + y_spaces))
                p2 = Point(p1.x + avg_width, p1.y + avg_height)
                self.facade_objects.append(FacadeObject(p1, p2, self.mode))
        self.grid_placed = 0
        self.image_label.update()

    def reject_grid_call(self):
        self.facade_objects.pop()
        self.facade_objects.pop()
        self.grid_placed = 0
        self.image_label.update()

    def mode_change_call(self, new_mode: str):
        if new_mode == 'Window':
            self.mode = FacObjTypes.WINDOW
        elif new_mode == 'Balcony':
            self.mode = FacObjTypes.BALCONY

    def grid_call(self):
        self.grid_mode = not self.grid_mode
        self.grid_placed = 0
        self.status_label.setText(self.grid_mode_text if self.grid_mode else self.standard_text)

    def finish_call(self):
        self.close()
        self.owner.insertIntoCAD(self.facade_objects)

    def undo_call(self):
        if len(self.facade_objects) > 0:
            self.deleted_objects.append(self.facade_objects.pop())
            self.grid_placed = max(self.grid_placed - 1, 0)
            self.image_label.update()

    def redo_call(self):
        if len(self.deleted_objects) > 0:
            self.facade_objects.append(self.deleted_objects.pop())
            self.grid_placed += 1
            self.image_label.update()


if __name__ == '__main__':
    app = QApplication([])
    FacadeGui(None, "/home/philip/workspace/baurobotik/flatten_facades/dev/Baurobotik/tum_transformed.png")
    app.exec()
