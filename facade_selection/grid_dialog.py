__author__ = "Philip Zimmermann"
__email__ = "philip.zimmermann@tum.de"
__version__ = "1.0"

try:
    from PySide.QtGui import QDialog, QFormLayout, QLineEdit, QPushButton, QIntValidator
except ModuleNotFoundError:
    from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton
    from PyQt5.QtGui import QIntValidator


class GridDialog(QDialog):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        form_layout = QFormLayout()

        self.qline_rows = QLineEdit('2')
        self.qline_columns = QLineEdit('2')
        self.qline_rows.setValidator(QIntValidator(1, 99))
        self.qline_columns.setValidator(QIntValidator(1, 99))

        accept_button = QPushButton('Complete Grid')
        accept_button.clicked.connect(self.accept)
        form_layout.addRow('Rows', self.qline_rows)
        form_layout.addRow('Columns', self.qline_columns)
        form_layout.addRow(accept_button)
        self.setLayout(form_layout)

    def reject(self) -> None:
        self.owner.reject_grid_call()
        super().reject()

    def accept(self) -> None:
        super(GridDialog, self).accept()
        self.owner.autocomplete_grid(int(self.qline_rows.text()), int(self.qline_columns.text()))
