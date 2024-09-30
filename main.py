import sys
import math
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QSlider, QTextEdit, QPushButton)
from PyQt6.QtGui import QPainter, QColor, QPolygon, QFont
from PyQt6.QtCore import Qt, QPoint, QTimer
import random
from datetime import datetime, timedelta

class HexagonWidget(QWidget):
    def __init__(self, title, color):
        super().__init__()
        self.title = title
        self.color = color
        self.value = "0"
        self.setMinimumSize(150, 150)

    def setValue(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
      
        center = self.rect().center()
        radius = min(self.width(), self.height()) // 2 - 10
        hexagon = QPolygon([
            center + QPoint(int(radius * math.cos(angle)), int(radius * math.sin(angle)))
            for angle in [i * 60 * math.pi / 180 for i in range(6)]
        ])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.color))
        painter.drawPolygon(hexagon)

        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, self.title)

        painter.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self.value}")

class PlantMonitorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plant Monitor")
        self.setGeometry(100, 100, 800, 600)
        self.watering_interval = 24  # Default watering interval in hours
        self.last_watered = datetime.now() - timedelta(hours=24)  # Initialize to 24 hours ago
        self.watering_history = []

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        title_label = QLabel("Automatic Plant Monitor")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        main_layout.addWidget(title_label)

        controls_layout = QHBoxLayout()

        self.interval_slider = QSlider(Qt.Orientation.Horizontal)
        self.interval_slider.setMinimum(1)
        self.interval_slider.setMaximum(72)
        self.interval_slider.setValue(self.watering_interval)
        self.interval_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.interval_slider.setTickInterval(12)
        self.interval_slider.valueChanged.connect(self.update_watering_interval)

        interval_layout = QVBoxLayout()
        interval_layout.addWidget(QLabel("Watering Interval (hours):"))
        interval_layout.addWidget(self.interval_slider)
        self.interval_label = QLabel(f"{self.watering_interval} hours")
        interval_layout.addWidget(self.interval_label)

        controls_layout.addLayout(interval_layout)

        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setMaximumHeight(100)
        history_layout = QVBoxLayout()
        history_layout.addWidget(QLabel("Watering History:"))
        history_layout.addWidget(self.history_text)

        controls_layout.addLayout(history_layout)
      
        self.water_button = QPushButton("Water Now")
        self.water_button.clicked.connect(self.manual_water)
        controls_layout.addWidget(self.water_button)

        main_layout.addLayout(controls_layout)

        hex_layout = QHBoxLayout()

        self.humidity_hex = HexagonWidget("Humidity", "#3498db")
        self.temperature_hex = HexagonWidget("Temperature", "#e74c3c")
        self.moisture_hex = HexagonWidget("Moisture", "#2ecc71")
        self.ph_hex = HexagonWidget("pH", "#f39c12")
        self.light_hex = HexagonWidget("Light", "#9b59b6")

        hex_layout.addWidget(self.humidity_hex)
        hex_layout.addWidget(self.temperature_hex)
        hex_layout.addWidget(self.moisture_hex)
        hex_layout.addWidget(self.ph_hex)
        hex_layout.addWidget(self.light_hex)

        main_layout.addLayout(hex_layout)
        self.setCentralWidget(central_widget)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateValues)
        self.timer.start(2000)  # Update every 2 seconds

    def update_watering_interval(self, value):
        self.watering_interval = value
        self.interval_label.setText(f"{value} hours")

    def manual_water(self):
        self.water_plant()

    def water_plant(self):
        current_time = datetime.now()
        self.last_watered = current_time
        self.watering_history.append(current_time.strftime("%Y-%m-%d %H:%M:%S"))
        self.update_history_text()

    def update_history_text(self):
        history_text = "\n".join(self.watering_history[-5:])  # Show last 5 watering times
        self.history_text.setText(history_text)

    def updateValues(self):
        self.humidity_hex.setValue(f"{random.randint(30, 80)}%")
        self.temperature_hex.setValue(f"{random.randint(15, 35)}°C")
        self.moisture_hex.setValue(f"{random.randint(20, 90)}%")
        self.ph_hex.setValue(f"{random.uniform(5.5, 7.5):.1f}")
        self.light_hex.setValue(f"{random.randint(100, 1000)} lux")

        if datetime.now() - self.last_watered > timedelta(hours=self.watering_interval):
            self.water_plant()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlantMonitorUI()
    window.show()
    sys.exit(app.exec())
