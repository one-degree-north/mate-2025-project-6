# Server (sensor_server.py)
import socket
import json
import random
import time

USE_RASPBERRY_PI = False  # Set this to True when running on Raspberry Pi

if USE_RASPBERRY_PI:
    import board
    import adafruit_dht
    import busio
    import adafruit_ads1x15.ads1015 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
    dht_sensor = adafruit_dht.DHT22(board.D4)
    MOISTURE_PIN = 17
    GPIO.setup(MOISTURE_PIN, GPIO.IN)
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1015(i2c)
    light_sensor = AnalogIn(ads, ADS.P0)
    ph_sensor = AnalogIn(ads, ADS.P1)
    moisture_sensor = AnalogIn(ads, ADS.P2)

def read_sensors():
    if USE_RASPBERRY_PI:
        try:
            temperature = dht_sensor.temperature
            humidity = dht_sensor.humidity
            moisture = moisture_sensor.value
            light = light_sensor.value
            ph = ph_sensor.voltage * 3.5

            moisture_percentage = (moisture - 1000) / (65535 - 1000) * 100
            moisture_percentage = max(0, min(100, moisture_percentage))

            return {
                "temperature": temperature,
                "humidity": humidity,
                "moisture": moisture_percentage,
                "light": light,
                "ph": ph
            }
        except Exception as e:
            print(f"Error reading sensor: {e}")
            return None
    else:
        return {
            "temperature": random.uniform(15, 35),
            "humidity": random.uniform(30, 80),
            "moisture": random.uniform(0, 100),
            "light": random.uniform(100, 1000),
            "ph": random.uniform(5.5, 7.5)
        }

def start_server():
    host = '127.0.0.1'  # localhost
    port = 65432

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"Server listening on {host}:{port}")
        
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    if data.decode() == "GET_DATA":
                        sensor_data = read_sensors()
                        conn.sendall(json.dumps(sensor_data).encode())
                    time.sleep(0.1)

if __name__ == "__main__":
    start_server()

# Client (plant_monitor_client.py)
import sys
import math
import json
import socket
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
        self.last_watered = datetime.now() - timedelta(hours=24)
        self.watering_history = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(('127.0.0.1', 65432))

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        title_label = QLabel("Automatic Plant Monitor with AI")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        main_layout.addWidget(title_label)

        self.plant_ai_text = QTextEdit()
        self.plant_ai_text.setReadOnly(True)
        self.plant_ai_text.setMaximumHeight(100)
        main_layout.addWidget(QLabel("Plant AI Says:"))
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
        
        if sensor_data['ph'] < 6.0:
            messages.append("The soil's a bit acidic. Maybe some lime would help?")
        elif sensor_data['ph'] > 7.0:
            messages.append("The soil's a bit alkaline. Perhaps some sulfur would balance things out?")
        
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
        try:
            self.socket.sendall("GET_DATA".encode())
            data = self.socket.recv(1024)
            sensor_data = json.loads(data.decode())
            
            self.humidity_hex.setValue(f"{sensor_data['humidity']:.1f}%")
            self.temperature_hex.setValue(f"{sensor_data['temperature']:.1f}°C")
            self.moisture_hex.setValue(f"{sensor_data['moisture']:.1f}%")
            self.ph_hex.setValue(f"{sensor_data['ph']:.1f}")
            self.light_hex.setValue(f"{sensor_data['light']:.0f} lux")

            plant_message = self.generate_plant_message(sensor_data)
            self.plant_ai_text.setText(plant_message)

            if datetime.now() - self.last_watered > timedelta(hours=24):
                self.water_plant()
        except Exception as e:
            print(f"Error updating values: {e}")

    def closeEvent(self, event):
        self.socket.close()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlantMonitorUI()
    window.show()
    sys.exit(app.exec())
