
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

class Card(QFrame):
    def __init__(self, name="Card"):
        super().__init__()
        self.setObjectName(name)

class AxisCard(Card):
    def __init__(self, title, colour):
        super().__init__("AxisCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(0)

        self.title = QLabel(title)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Arial", 12, QFont.Bold))

        self.value = QLabel("0.0")
        self.value.setAlignment(Qt.AlignCenter)
        self.value.setFont(QFont("Arial", 29, QFont.Bold))
        self.value.setStyleSheet(f"color: {colour};")

        self.target = QLabel("Target: 0.0")
        self.target.setAlignment(Qt.AlignCenter)
        self.target.setFont(QFont("Arial", 10, QFont.Bold))

        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.target)
