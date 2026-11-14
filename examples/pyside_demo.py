"""PySide6 / PyQt6: re-scale on resize and on moving to another monitor."""
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout

import appdimens as ad
from appdimens.integrations import metrics_from_qt


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.scope = ad.Dimens()
        self.label = QLabel("Hello, AppDimens")
        lay = QVBoxLayout(self)
        lay.addWidget(self.label)
        self.resize(360, 640)

    def resizeEvent(self, e):  # noqa: N802
        self.scope.set_metrics(metrics_from_qt(self))
        s = self.scope
        self.layout().setContentsMargins(*[int(s.sdp(16))] * 4)
        self.label.setStyleSheet("font-size: %dpx;" % round(s.assp(18)))
        super().resizeEvent(e)


app = QApplication([])
w = Window()
w.show()
app.exec()
