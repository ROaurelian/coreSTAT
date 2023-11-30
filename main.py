import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
import serial.tools.list_ports
import serial
from mainWindow import Ui_MainWindow
import time

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

        self.currentwidget.setLabel("left", "Corriente (uA)")
        self.currentwidget.setLabel("bottom", "Voltaje (V)")
        self.currentwidget.setYRange(-200, 200)
        self.currentwidget.setXRange(-1.0, 1.0)

        self.potentialwidget.setLabel("left", "Voltaje (V)")
        self.potentialwidget.setLabel("bottom", "Tiempo (s)")

        self.startButton.clicked.connect(self.startClick)
        self.cancelButton.clicked.connect(self.stopClick)

    def startClick(self):
        self.startButton.setEnabled(False)

        # Params checking
        minPotential = -1.00
        maxPotential = 1.00
        minRange = 0.10

        baudrate = self.baudratecomboBox.currentText()

        # LImitation of sampling rate based on baud rate
        maxSamplingRate = 0
        if baudrate == "9600":
            maxSamplingRate = 0.96
        elif baudrate == "19200":
            maxSamplingRate = 1.92
        elif baudrate == "57600":
            maxSamplingRate = 5.76
        elif baudrate == "115200":
            maxSamplingRate = 11.52

        if float(self.samplingcomboBox.currentText()) > maxSamplingRate:
            self.statusBar().showMessage(f"Velocidad de muestreo no válida (Máxima velocidad de muestreo: {maxSamplingRate}) kS/s")
            self.startButton.setEnabled(True)
            return

        try:
            lowerRange = round(float(self.lowerrangelineEdit.text()), 2)
            upperRange = round(float(self.upperrangelineEdit.text()), 2)
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

        self.statusBar().showMessage("Conectando...")

        # Serial connection routine
        port = self.portcomboBox.currentText()
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
        time.sleep(2)  # Wait for the connection to initialize

        data = bytearray(self.format_data())
        self.write_to_serial(data)
        self.read_from_serial()

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

    def write_to_serial(self, data):
        if self.serialPortHandle.isOpen():
            try:
                self.serialPortHandle.write(data)
            except serial.SerialException as e:
                self.statusBar().showMessage(f"Error: {e}")

    def format_data(self):
        # The first 2 bits are for the mode (0-3)
        # The next 4 bits are for the scan rate (0-15)
        # The next 4 bits are for the sampling rate (0-15)
        # The next 8 bits are for the lower range (-1.0-1.0)
        # The next 8 bits are for the upper range (-1.0-1.0)

        scanRate = self.speedcomboBox.currentIndex()
        samplingRate = self.samplingcomboBox.currentIndex()
        mode = self.modecomboBox.currentIndex()
        lowerRange = round(float(self.lowerrangelineEdit.text()), 2)
        upperRange = round(float(self.upperrangelineEdit.text()), 2)

        frame1 = 0x00
        frame1 = frame1 | (mode << 4)
        frame1 = frame1 | (scanRate)
        frame3 = int((1 + lowerRange) * 127)
        frame4 = int((1 + upperRange) * 127)
        return [frame1, samplingRate, frame3, frame4]

    def stopClick(self):
        self.statusBar().showMessage("Cancelando...")
        if self.serialPortHandle and self.serialPortHandle.isOpen():
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
