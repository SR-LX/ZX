from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QSize, Qt

class GradientButton(QPushButton):
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #66a6ff, stop: 1 #89f7fe);
                border-style: outset;
                border-width: 3px;
                border-radius: 8px;
                border-color: #4d90fe;
                color: white;
                padding: 5px;
                min-width: 50px;
                min-height: 10px;
            }
            
            QPushButton:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #4d90fe, stop: 1 #73e0e9);
            }
            
            QPushButton:pressed {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #357ae8, stop: 1 #56b9c1);
                border-style: inset;
            }
        """)