from datetime import datetime as dt
from functools import partial

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QPushButton, QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox, \
    QGroupBox

from myqgroupbox import DeviceGB, AlarmGB, EyeButton


class Acquisition(QPushButton):
    TIMEOUT = 90

    def __init__(self, module):
        QPushButton.__init__(self, "ACQUISITION")

        self.module = module
        self.networkError = False

        self.setColorText("ACQUISITION", "green", 160)
        self.getTimeout()

        self.dialog = self.dialogTimeout()
        self.dialog.hide()
        self.clicked.connect(self.dialog.show)

    @property
    def devices(self):
        return [dev["tablename"] for dev in self.module.devices]

    @property
    def mainWindow(self):
        return self.module.mainWindow

    def getTimeout(self):
        self.timeout_ack = []
        self.list_timeout = [d for d in self.devices]
        self.last_date = {}
        self.last_time = {}
        for device in self.devices:
            self.last_date[device] = 0
            self.last_time[device] = dt.now()

        timeoutChecker = QTimer(self.mainWindow)
        timeoutChecker.setInterval(7000)
        timeoutChecker.timeout.connect(self.checkTimeout)
        timeoutChecker.start()

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
            checkbox.stateChanged.connect(partial(self.ackTimeout, checkbox))
            checkbox.setCheckState(2)
            grid.addWidget(checkbox, 1 + i, 0, 1, 3)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.button(QDialogButtonBox.Ok).clicked.connect(d.hide)
        buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(d.hide)
        vbox.addLayout(grid)
        vbox.addWidget(buttonBox)
        d.setLayout(vbox)
        return d

    def ackTimeout(self, checkbox):
        if checkbox.isChecked():
            if str(checkbox.text()) in self.timeout_ack:
                self.timeout_ack.remove(str(checkbox.text()))
        else:
            self.timeout_ack.append(str(checkbox.text()))

    def timeoutShow(self, i=0):
        timeoutShow = QTimer(self.mainWindow)
        timeoutShow.singleShot(3000, partial(self.showTimeout, i))

    def showTimeout(self, i):
        for timeout in self.timeout_ack:
            try:
                self.list_timeout.remove(timeout)
            except ValueError:
                pass
        if not self.networkError:
            if self.list_timeout:
                if i < len(self.list_timeout):
                    self.setColorText("TIME OUT ON %s" % self.list_timeout[i], "red", 300)
                    i += 1
                else:
                    i = 0
            else:
                self.setColorText("ACQUISITION", "green", 160)
        else:
            self.setColorText("SERVER LOST", "orange", 160)
        self.timeoutShow(i)

    def checkTimeout(self):

        for device in self.devices:
            return_values = self.mainWindow.db.getLastData(device, "id")
            if return_values == -5:
                self.networkError = True
            elif type(return_values) is int:
                self.mainWindow.showError(return_values)
            else:
                date, id = return_values
                self.networkError = False

                if date != self.last_date[device]:
                    if self.last_date[device] != 0:
                        if device in self.list_timeout:
                            self.list_timeout.remove(device)
                    self.last_time[device] = dt.now()
                    self.last_date[device] = date
                else:
                    if (dt.now() - self.last_time[device]).total_seconds() > Acquisition.TIMEOUT:
                        if device not in self.list_timeout:
                            self.list_timeout.append(device)

    def setColorText(self, text, color, size):
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

        self.setFixedSize(size, 36)


class Module(QGroupBox):
    def __init__(self, mainWindow, name, devices, alarms):
        QGroupBox.__init__(self)
        self.setTitle(name)

        self.mainWindow = mainWindow
        self.name = name
        self.devices = devices
        self.alarms = alarms

        self.groupBox = []
        self.alarmGB = []
        self.divcoeff = 3

        self.cLayout = QHBoxLayout()
        self.alarmLayout = QHBoxLayout()
        self.gbLayout = QGridLayout()

        self.cLayout.addLayout(self.alarmLayout)
        self.cLayout.addLayout(self.gbLayout)

        self.setLayout(self.cLayout)

        self.initialize()
        self.waitforData()

        self.timerData = QTimer(self)
        self.timerData.setInterval(3000)
        self.timerData.timeout.connect(self.waitforData)
        self.timerData.start()

    def initialize(self):
        self.createGroupBox()
        self.eyeButton = EyeButton(self)
        self.createAlarms()

    def moveEye(self):

        try:
            self.eyeButton.move(self.width() - 30, 0)
        except:
            pass

    def createGroupBox(self):
        for i, boxes in enumerate(self.devices):
            tableName = boxes["tablename"]
            deviceName = boxes["label_device"]
            keys = boxes["key"].split(',')
            labels = boxes["label"].split(',')
            units = boxes["unit"].split(',')
            lowBounds = boxes["lower_bound"].split(',')
            upBounds = boxes["higher_bound"].split(',')

            self.groupBox.append(DeviceGB(self, tableName, deviceName, keys, labels, units, lowBounds, upBounds))
            self.gbLayout.addWidget(self.groupBox[-1], (i // self.divcoeff) + 1, i % self.divcoeff)

    def createAlarms(self):

        self.acquisition = Acquisition(self)
        self.alarmLayout.addWidget(self.acquisition)

        for alarm in self.alarms:
            self.alarmGB.append(AlarmGB(self, alarm))
            self.alarmLayout.addWidget(self.alarmGB[-1])

    def showAll(self, bool):

        for groupbox in self.groupBox:
            if not bool:
                groupbox.hide()
            else:
                groupbox.show()

        for alarm in self.alarmGB:
            if not bool:
                alarm.show()
            else:
                alarm.hide()

        if bool:
            self.setMaximumHeight(500)
        else:
            self.setMaximumHeight(80)
            self.mainWindow.resize(20, 20)

    def showhideConfig(self, button_arrow):

        if not self.groupBox[0].isHidden():
            self.showAll(False)
            button_arrow.setIcon(self.mainWindow.iconArrRight)

        else:
            self.showAll(True)
            button_arrow.setIcon(self.mainWindow.iconArrLeft)

    def waitforData(self):
        for groupbox in self.groupBox:
            groupbox.waitforData()
        for alarm in self.alarmGB:
            alarm.getValue()

    def resizeEvent(self, QResizeEvent):
        self.moveEye()
        QGroupBox.resizeEvent(self, QResizeEvent)