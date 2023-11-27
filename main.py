import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
import serial.tools.list_ports
import serial
from mainWindow import Ui_MainWindow
import numpy as np
import math

num_elements = 1400  # number of elements in each array
v_start = -1.0       # start voltage
v_end = 1.0          # end voltage      

# Function to simulate current response with a sigmoidal shape and peak
def simulate_current(v_array, peak_pos, peak_height, peak_width):
    # Simulate redox peak
    gauss = peak_height * np.exp(-((v_array - peak_pos) ** 2) / (2 * peak_width ** 2))
    log_argument = v_array - peak_pos
    log_argument[log_argument <= 0] = np.min(v_array[v_array > 0])
    log = 10*np.log(log_argument)+peak_height/2
    return gauss + log

def add_noise_with_max_error(current_array, max_error_percent=4):
    max_error = max_error_percent / 100.0
    # Calculate the noise level for each point (5% of the current value)
    noise_level = max_error * current_array
    # Generate random noise within the ±5% range for each point
    noise = np.random.uniform(-1, 1, size=current_array.shape) * noise_level
    # Add this noise to the original current values
    noisy_current = current_array + noise
    return noisy_current

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.serialPortHandle = None
        self.windowRefreshTimer = QTimer(self) 
        self.windowRefreshTimer.timeout.connect(self.listComPorts)
        self.windowRefreshTimer.start(500)
        self.statusBar().showMessage("Desconectado") 

        self.lowerrangelineEdit.setText(str(-1.00))
        self.upperrangelineEdit.setText(str(1.00))

        self.startButton.clicked.connect(self.startClick)
        self.cancelButton.clicked.connect(self.stopClick)

    def startClick(self):
        self.statusBar().showMessage("Conectando...")
        self.startButton.setEnabled(False)

        # Serial connection routine
        port = self.portcomboBox.currentText()
        baudrate = self.baudratecomboBox.currentText()
        if port == "":
            self.statusBar().showMessage("Ningún puerto disponible")
            self.startButton.setEnabled(True)
            return
        try:
            self.serialPortHandle = serial.Serial(port, baudrate = int(baudrate), timeout=1)
            self.statusBar().showMessage(f"Conectado a {port}")
        except:
            self.statusBar().showMessage(f"Error conectando a {port}")
            self.startButton.setEnabled(True)

        # Params checking
        minPotential = -1.00
        maxPotential = 1.00
        minRange = 0.10

        scanRate = int(self.speedcomboBox.currentText())
        samplingRate = int(self.samplingcomboBox.currentText())
        mode = int(self.modecomboBox.currentIndex())

        try:
            lowerRange = round(float(self.lowerrangelineEdit.text()), 1)
            upperRange = round(float(self.upperrangelineEdit.text()), 1)
        except:
            self.statusBar().showMessage("Valores de rango no válidos")
            self.startButton.setEnabled(True)
            return
        if lowerRange < minPotential or upperRange > maxPotential:
            self.statusBar().showMessage(f"Fuera de rango de potencial ({minPotential}V a {maxPotential}V)")
            self.startButton.setEnabled(True)
            return
        if upperRange - lowerRange <= minRange:
            self.statusBar().showMessage(f"Valores de rango no válidos (Mínimo rango de {minRange}V)")
            self.startButton.setEnabled(True)
            return
        
        self.lowerrangelineEdit.setText(str(lowerRange))
        self.upperrangelineEdit.setText(str(upperRange))

        # Generate voltage array with a linear sweep forward and reverse
        voltage_array = np.linspace(v_start, v_end, num_elements)
        
        peak_height = [160, 150, 130, 100, 75]
        peak_pos = [-0.15, -0.16, -0.17, -0.18, -0.19]

        current_arrays = []
        for i in range(5):  # Simulate 5 different scan rates
            peak_width = 0.05 + i*0.01  # Change the peak width for each scan rate
            current = simulate_current(voltage_array, peak_pos[i], peak_height[i], peak_width)
            noisy_current_array = add_noise_with_max_error(current)
            current_arrays.append(noisy_current_array)

        # Make sure all arrays have 1400 elements
        voltage_array = np.tile(voltage_array, (int(np.ceil(1400/len(voltage_array))),))[:1400]
        current_arrays = [np.tile(i, (int(np.ceil(1400/len(i))),))[:1400] for i in current_arrays]
        self.currentwidget.plot(voltage_array, current_arrays[0])
        self.potentialwidget.plot(voltage_array)

    """     self.serialReadTimer = QTimer(self)
        self.serialReadTimer.timeout.connect(self.read_from_serial)
        self.serialReadTimer.start(20) """
    
    def read_from_serial(self):
        if self.serialPortHandle.isOpen():
            try:
                data = self.serialPortHandle.readline().decode().strip()
                if data:
                    self.statusBar().showMessage(data)
            except serial.SerialException as e:
                self.statusBar().showMessage(f"Error: {e}")

    def stopClick(self):
        self.statusBar().showMessage("Cancelando...")
        if self.serialPortHandle.isOpen():
            self.serialPortHandle.close()
        self.startButton.setEnabled(True)
        self.statusBar().showMessage("Desconectado")

    def listComPorts(self):
        current_ports = set([self.portcomboBox.itemText(i) for i in range(self.portcomboBox.count())])
        available_ports = set([f"{port}" for port, desc, hwid in serial.tools.list_ports.comports()])

        new_ports = available_ports - current_ports
        removed_ports = current_ports - available_ports

        # Add new ports that were not in the combo box
        for port in new_ports:
            self.portcomboBox.addItem(port)

        # Remove ports that are no longer available
        for port in removed_ports:
            index = self.portcomboBox.findText(port)
            if index >= 0:
                self.portcomboBox.removeItem(index)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
