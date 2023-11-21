import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
import serial.tools.list_ports
import serial
from mainWindow import Ui_MainWindow

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.serialPortHandle = None
        self.windowRefreshTimer = QTimer(self) 
        self.windowRefreshTimer.timeout.connect(self.listComPorts)
        self.windowRefreshTimer.start(500)
        self.statusBar().showMessage("Desconectado") 

        self.startButton.clicked.connect(self.startClick)
        self.cancelButton.clicked.connect(self.stopClick)

    def startClick(self):
        self.statusBar().showMessage("Conectando...")
        self.startButton.setEnabled(False)
        port = self.portcomboBox.currentText()
        baudrate = self.baudratecomboBox.currentText()
        if port == "":
            self.statusBar().showMessage("Ningún puerto disponible")
            return
        try:
            self.serialPortHandle = serial.Serial(port, baudrate = int(baudrate), timeout=1)
            self.statusBar().showMessage(f"Conectado a {port}")
        except:
            self.statusBar().showMessage(f"Error conectando a {port}")
            self.startButton.setEnabled(True)
        self.serialReadTimer = QTimer(self)
        self.serialReadTimer.timeout.connect(self.read_from_serial)
        self.serialReadTimer.start(500)
    
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
