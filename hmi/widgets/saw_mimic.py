
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QFont

class SawMimic(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(145)
        self.fence = 1250.0
        self.height = 78.0
        self.tilt = 90.0

    def set_values(self, fence, height, tilt):
        self.fence = fence
        self.height = height
        self.tilt = tilt
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        p.fillRect(self.rect(), QColor("#0b121a"))

        p.setPen(QPen(QColor("#52677a"), 2))
        p.setBrush(QColor("#253442"))
        p.drawRoundedRect(20, 38, int(w * 0.64), 42, 4, 4)

        p.setPen(QPen(QColor("#aab6c1"), 4))
        p.drawLine(35, 55, int(w * 0.67), 55)
        p.drawLine(35, 70, int(w * 0.67), 70)

        p.setBrush(QColor("#d2d7dc"))
        p.setPen(QPen(QColor("#74808c"), 2))
        saw_x = int(w * 0.34)
        p.drawEllipse(saw_x, 22, 58, 58)

        p.setBrush(QColor("#c6cbd0"))
        p.drawRect(70, 82, 75, 42)
        p.drawRect(int(w * 0.56), 82, 75, 42)

        p.setPen(QColor("#f2f5f7"))
        p.setFont(QFont("Arial", 18, QFont.Bold))
        p.drawText(155, 110, "SCM")

        fence_x = 35 + int(min(max(self.fence / 3200.0, 0), 1) * 180)
        p.setPen(QPen(QColor("#b5c0ca"), 3))
        p.drawLine(fence_x, 25, fence_x, 132)
        p.drawLine(fence_x - 30, 42, fence_x + 36, 42)
        p.drawRect(fence_x - 10, 75, 20, 35)

        p.setPen(QPen(QColor("#31a32a"), 1))
        p.setBrush(QColor("#31a32a"))
        p.drawRect(int(w * 0.62), 25, 12, 12)
        p.setBrush(QColor("#c92820"))
        p.drawRect(int(w * 0.62), 12, 12)
