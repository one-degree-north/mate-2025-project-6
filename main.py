import sys
import math
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTextEdit, QPushButton)
from PyQt6.QtGui import QPainter, QColor, QPolygon, QFont
from PyQt6.QtCore import Qt, QPoint, QTimer
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
        self.last_watered = datetime.now() - timedelta(hours=24)  # Initialize to 24 hours ago
        self.watering_history = []

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        title_label = QLabel("Automatic Plant Monitor")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        main_layout.addWidget(title_label)

        self.plant_ai_text = QTextEdit()
        self.plant_ai_text.setReadOnly(True)
        self.plant_ai_text.setMaximumHeight(100)
        main_layout.addWidget(QLabel("Plant Says:"))
        main_layout.addWidget(self.plant_ai_text)

        controls_layout = QHBoxLayout()

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
        self.timer.start(2000) 

    def generate_plant_message(self, sensor_data):
        messages = []
        if sensor_data['temperature'] > 30:
            messages.append("Whew, it's getting hot in here!")
        elif sensor_data['temperature'] < 20:
            messages.append("Brr, I'm feeling a bit chilly.")
        
        if sensor_data['humidity'] < 40:
            messages.append("I'm feeling a bit dry. Could use some mist!")
        elif sensor_data['humidity'] > 70:
            messages.append("It's quite humid today. I feel like I'm in a rainforest!")
        
        if sensor_data['moisture'] < 30:
            messages.append("I'm thirsty! Could you water me, please?")
        elif sensor_data['moisture'] > 80:
            messages.append("Whoa, easy on the water there! I'm not a fish.")
        
        if sensor_data['light'] < 300:
            messages.append("It's a bit dark here. I could use some more light to grow.")
        elif sensor_data['light'] > 800:
            messages.append("Wow, it's bright! I feel like I'm on a beach vacation.")
        
        if not messages:
            messages.append("Everything's just perfect! I'm one happy plant!")
        
        return random.choice(messages)

    def manual_water(self):
        self.water_plant()

    def water_plant(self):
        current_time = datetime.now()
        self.last_watered = current_time
        self.watering_history.append(current_time.strftime("%Y-%m-%d %H:%M:%S"))
        self.update_history_text()

    def update_history_text(self):
        history_text = "\n".join(self.watering_history[-5:])  
        self.history_text.setText(history_text)

    def updateValues(self):
        sensor_data = {
            'humidity': random.randint(30, 80),
            'temperature': random.randint(20, 25),
            'moisture': random.randint(50, 70),
            'ph': round(random.uniform(5.5, 7.5), 1),
            'light': random.randint(100, 1000)
        }

        self.humidity_hex.setValue(f"{sensor_data['humidity']}%")
        self.temperature_hex.setValue(f"{sensor_data['temperature']}°C")
        self.moisture_hex.setValue(f"{sensor_data['moisture']}%")
        self.ph_hex.setValue(f"{sensor_data['ph']}")
        self.light_hex.setValue(f"{sensor_data['light']} lux")

        plant_message = self.generate_plant_message(sensor_data)
        self.plant_ai_text.setText(plant_message)

        if datetime.now() - self.last_watered > timedelta(hours=24):
            self.water_plant()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlantMonitorUI()
    window.show()
    sys.exit(app.exec())
