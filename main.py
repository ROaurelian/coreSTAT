import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
import serial.tools.list_ports
import serial
from mainWindow import Ui_MainWindow
import time
import numpy as np
import pyqtgraph as pg

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.colorIndex = 0
        self.colors = ['r', 'g', 'b', 'c', 'm', 'y']
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
        self.clearButton.clicked.connect(self.clearClick)

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
            maxSamplingRate = 0.48
        elif baudrate == "19200":
            maxSamplingRate = 0.96
        elif baudrate == "57600":
            maxSamplingRate = 2.88
        elif baudrate == "115200":
            maxSamplingRate = 5.76

        if float(self.samplingcomboBox.currentText()) > maxSamplingRate:
            self.statusBar().showMessage(f"Velocidad de muestreo no válida con baudrate (Máxima velocidad de muestreo: {maxSamplingRate}) kS/s")
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

        # Send voltage values to apply to the serial port
        self.plotPotential()
        self.statusBar().showMessage("Recibiendo...")
        self.period = round(float(1/(self.samplingRate*1000)),3)
        voltagePWM = (self.voltage_array + 1) * 127
        for i in range(len(voltagePWM)):
            self.write_to_serial(bytes([int(voltagePWM[i])]))
            time.sleep(self.period)
            # self.read_from_serial()



    """     self.serialReadTimer = QTimer(self)
        self.serialReadTimer.timeout.connect(self.read_from_serial)
        self.serialReadTimer.start(20) """
    

    
    def plotPotential(self):
        v_start = round(float(self.lowerrangelineEdit.text()), 2)
        v_end = round(float(self.upperrangelineEdit.text()), 2)
        scanRate = int(self.speedcomboBox.currentText())
        self.samplingRate = float(self.samplingcomboBox.currentText())
        time = (v_end - v_start) / (scanRate/1000)
        mode = self.modecomboBox.currentIndex()
        num_elements = int(time * self.samplingRate * 1000)
        time_array = np.linspace(0, time, num_elements)

        if mode == 0:
            self.voltage_array = np.linspace(v_start, v_end, num_elements)
        elif mode == 1:
            first_half = np.linspace(v_start, v_end, int(num_elements/2)) 
            second_half = np.linspace(v_end, v_start, int(num_elements/2))
            self.voltage_array = np.concatenate((first_half, second_half))

        color = self.colors[self.colorIndex % len(self.colors)]
        self.potentialwidget.plot(time_array, self.voltage_array, pen=pg.mkPen(color))
        return 

    def plotCurrent(self):
        self.colorIndex += 1
    
    def read_from_serial(self):
        if self.serialPortHandle.isOpen():
            try:
                data = self.serialPortHandle.readline().decode().strip()
                if data:
                    self.statusBar().showMessage(f'Intruction set: {data}')
            except serial.SerialException as e:
                self.statusBar().showMessage(f"Error: {e}")

    def write_to_serial(self, data):
        if self.serialPortHandle.isOpen():
            try:
                self.serialPortHandle.write(data)
            except serial.SerialException as e:
                self.statusBar().showMessage(f"Error: {e}")

    def stopClick(self):
        self.statusBar().showMessage("Cancelando...")
        if self.serialPortHandle and self.serialPortHandle.isOpen():
            self.serialPortHandle.close()
        self.startButton.setEnabled(True)
        self.statusBar().showMessage("Desconectado")


    def clearClick(self):      
        self.potentialwidget.clear()
        self.currentwidget.clear()

        self.currentwidget.setLabel("left", "Corriente (uA)")
        self.currentwidget.setLabel("bottom", "Voltaje (V)")
        self.currentwidget.setYRange(-200, 200)
        self.currentwidget.setXRange(-1.0, 1.0)

        self.potentialwidget.setLabel("left", "Voltaje (V)")
        self.potentialwidget.setLabel("bottom", "Tiempo (s)")
        

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
