import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
import serial.tools.list_ports
from mainWindow import Ui_MainWindow

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.timer = QTimer(self) 
        self.timer.timeout.connect(self.listComPorts)
        self.timer.start(500) 

        self.startButton.clicked.connect(self.startClick)

    def startClick(self):
        print("Button was clicked!")

    def listComPorts(self):
        current_ports = set([self.portcomboBox.itemText(i) for i in range(self.portcomboBox.count())])
        available_ports = set([f"{port} - {desc}" for port, desc, hwid in serial.tools.list_ports.comports()])

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
