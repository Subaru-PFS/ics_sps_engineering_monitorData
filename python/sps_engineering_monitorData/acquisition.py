__author__ = 'alefur'

from functools import partial
import time

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QGridLayout, QPushButton, QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox, QSizePolicy

from sps_engineering_Lib_dataQuery.confighandler import readTimeout, writeTimeout


class Acquisition(QPushButton):
    TIMEOUT = 90

    def __init__(self, module):
        QPushButton.__init__(self, "ACQUISITION")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setMinimumHeight(35)
        self.module = module
        self.network = True

        self.setColorText("     ACQUISITION     ", "green")

        self.list_timeout = []
        self.last_date = {}
        self.last_time = {}
        self.getTimeout()

        self.dialog = self.dialogTimeout()
        self.dialog.hide()
        self.clicked.connect(self.dialog.show)

    @property
    def devices(self):
        return [device.tablename for device in self.module.devices]

    @property
    def mainWindow(self):
        return self.module.mainWindow

    @property
    def vistimeout(self):
        return [timeout for timeout in self.list_timeout if timeout not in self.timeout_ack]

    @property
    def aliveDevices(self):
        return [device for device in self.devices if device not in self.list_timeout]

    @property
    def timeout_ack(self):
        return readTimeout()

    def getTimeout(self):
        self.list_timeout = [d for d in self.devices]

        for device in self.devices:
            self.last_date[device] = 0
            self.last_time[device] = time.time()

        self.timeoutShow()

    def dialogTimeout(self):
        d = QDialog(self.mainWindow)
        d.setFixedWidth(450)
        d.setWindowTitle("Setting Devices Timeout")
        d.setVisible(True)
        vbox = QVBoxLayout()
        grid = QGridLayout()
        grid.setSpacing(20)

        for i, device in enumerate(self.devices):
            checkbox = QCheckBox(device)
            checkbox.setCheckState(0) if device in self.timeout_ack else checkbox.setCheckState(2)
            checkbox.stateChanged.connect(partial(self.ackTimeout, checkbox))

            grid.addWidget(checkbox, 1 + i, 0, 1, 3)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.button(QDialogButtonBox.Ok).clicked.connect(d.hide)
        buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(d.hide)
        vbox.addLayout(grid)
        vbox.addWidget(buttonBox)
        d.setLayout(vbox)
        return d

    def ackTimeout(self, checkbox):
        timeout_ack = self.timeout_ack

        if checkbox.isChecked():
            if str(checkbox.text()) in timeout_ack:
                timeout_ack.remove(str(checkbox.text()))
        else:
            timeout_ack.append(str(checkbox.text()))

        writeTimeout(timeout_ack)

    def timeoutShow(self, i=0):
        timeoutShow = QTimer(self.mainWindow)
        timeoutShow.singleShot(3000, partial(self.showTimeout, i))

    def showTimeout(self, i):
        if self.network:
            if self.vistimeout:
                if i < len(self.vistimeout):
                    self.setColorText("TIME OUT ON %s" % self.vistimeout[i], "red")
                    i += 1
                else:
                    i = 0
            else:
                if self.aliveDevices and not self.module.isOffline:
                    self.setColorText("     ACQUISITION     ", "green")
                else:
                    self.setColorText("     OFFLINE     ", "red")

        else:
            self.setColorText("     SERVER LOST     ", "orange")

        self.timeoutShow(i)

    def checkTimeout(self, table, tai=False):
        tai = tai if tai else self.last_date[table]
        if tai != self.last_date[table]:
            if self.last_date[table] != 0:
                if table in self.list_timeout:
                    self.list_timeout.remove(table)

            self.last_time[table] = time.time()
            self.last_date[table] = tai
        else:
            if (time.time() - self.last_time[table]) > Acquisition.TIMEOUT:
                if table not in self.list_timeout:
                    self.list_timeout.append(table)

        if table in self.list_timeout:
            self.module.getGroupBox(table).setOffline()
        else:
            self.module.getGroupBox(table).setOnline()

    def setColorText(self, text, color):
        self.setText(text)

        if color == "green":
            self.setStyleSheet(
                "QPushButton { color : white; background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #45f42e, stop: 1 #195511);border-radius: 6px; font: 12pt;}")
        elif color == "red":
            self.setStyleSheet(
                "QPushButton { color : white; background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #f43131, stop: 1 #5e1414) ;border-radius: 6px; font: 12pt;}")

        elif color == "orange":
            self.setStyleSheet(
                "QPushButton { color : white; background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.7, fy:0.5, stop:0 rgba(255,190,0, 90%), stop:1 rgba(255,130,0, 90%));border-radius: 9px; font: 13pt;}")

