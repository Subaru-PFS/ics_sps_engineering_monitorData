__author__ = 'alefur'

from functools import partial
import time

from PyQt5.QtGui import QPixmap, QIcon, QCursor
from PyQt5.QtWidgets import QLabel, QMenu, QAction
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QGridLayout, QPushButton, QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox, \
    QGroupBox


class EyeButton(QPushButton):
    def __init__(self, module):
        QPushButton.__init__(self)
        self.module = module
        self.setParent(module)
        eyeOn = QPixmap()
        eyeOff = QPixmap()

        eyeOn.load('%s/%s' % (module.mainWindow.imgPath, 'eye_on.png'))
        eyeOff.load('%s/%s' % (module.mainWindow.imgPath, 'eye_off.png'))
        self.iconEyeOn = QIcon(eyeOn)
        self.iconEyeOff = QIcon(eyeOff)

        self.mainWindow = module.mainWindow
        self.setFixedSize(30, 20)
        self.showGB()
        self.clicked.connect(self.showGB)

    def showGB(self):
        if self.module.groupBox[0].isHidden():
            self.setIcon(self.iconEyeOff)
            self.module.showAll(True)

        else:
            self.setIcon(self.iconEyeOn)
            self.module.showAll(False)


class Acquisition(QPushButton):
    TIMEOUT = 90

    def __init__(self, module):
        QPushButton.__init__(self, "ACQUISITION")
        self.module = module
        self.network = True

        self.setColorText("ACQUISITION", "green", 160)

        self.list_timeout = []
        self.last_date = {}
        self.last_time = {}
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

    @property
    def vistimeout(self):
        return [timeout for timeout in self.list_timeout if timeout not in self.timeout_ack]

    @property
    def aliveDevices(self):
        return [device for device in self.devices if device not in self.list_timeout]

    @property
    def timeout_ack(self):
        return self.module.unPickle('timeoutAck', empty='list')

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

        self.module.doPickle('timeoutAck', timeout_ack)

    def timeoutShow(self, i=0):
        timeoutShow = QTimer(self.mainWindow)
        timeoutShow.singleShot(3000, partial(self.showTimeout, i))

    def showTimeout(self, i):
        if self.network:
            if self.vistimeout:
                if i < len(self.vistimeout):
                    self.setColorText("TIME OUT ON %s" % self.vistimeout[i], "red", 300)
                    i += 1
                else:
                    i = 0
            else:
                if self.aliveDevices:
                    self.setColorText("ACQUISITION", "green", 160)
                else:
                    self.setColorText("OFFLINE", "red", 160)

        else:
            self.setColorText("SERVER LOST", "orange", 160)

        self.timeoutShow(i)

    def checkTimeout(self, table, tai):

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


class AlarmGB(QGroupBox):
    def __init__(self, module, alarm):
        self.module = module
        self.alarm = alarm

        if "gatevalve" in alarm["tablename"]:
            self.stateGatevalve = {0: "OPEN", 1: "CLOSED", 2: "UNKNOWN", 3: "INVALID"}

        QGroupBox.__init__(self)
        self.setTitle(alarm["label"])

        self.grid = QGridLayout()
        self.value = QLabel()

        self.grid.addWidget(self.value, 0, 0)
        self.setLayout(self.grid)
        self.value.setStyleSheet("QLabel{font-size: 11pt; qproperty-alignment: AlignCenter; color:white;}")
        self.getValue()

    @property
    def isEffective(self):

        listAlarm = self.module.unPickle('listAlarm')
        return listAlarm[self.name]

    @property
    def name(self):
        return self.alarm["label"].lower()

    def setColor(self, color):
        if color == "red":
            self.setStyleSheet(
                "QGroupBox {font-size: 9pt; background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #f43131, stop: 1 #5e1414);border: 1px solid gray;border-radius: 3px;margin-top: 1ex;} " +
                "QGroupBox::title {subcontrol-origin: margin;subcontrol-position: top center; padding: 0 3px;}")
        elif color == "green":
            self.setStyleSheet(
                "QGroupBox {font-size: 9pt; background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #45f42e, stop: 1 #195511);border: 1px solid gray;border-radius: 3px;margin-top: 1ex;} " +
                "QGroupBox::title {subcontrol-origin: margin;subcontrol-position: top center; padding: 0 3px;}")

        elif color == "black":
            self.setStyleSheet(
                "QGroupBox {font-size: 9pt; background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop:0 rgba(40,40,40, 90%), stop:1 rgba(0,0,0, 90%));border: 1px solid gray;border-radius: 3px;margin-top: 1ex;} " + "QGroupBox::title {subcontrol-origin: margin;subcontrol-position: top center; padding: 0 3px;}")

    def getValue(self):
        dataFrame = self.module.mainWindow.db.last(self.alarm["tablename"], self.alarm["key"])

        try:
            val = dataFrame[self.alarm["key"]]
            if self.isEffective:
                if not (float(self.alarm["lower_bound"]) <= val < float(self.alarm["upper_bound"])):
                    self.setColor("red")
                else:
                    self.setColor("green")
            else:
                self.setColor("black")

            txt = '{:g}'.format(val) if not hasattr(self, "stateGatevalve") else self.stateGatevalve[val]

        except TypeError:
            txt = 'nan'

        self.value.setText(txt)

    def mouseReleaseEvent(self, QMouseEvent):
        if QMouseEvent.button() == Qt.RightButton:
            menu = QMenu(self)

            action = QAction('Desactivate', self) if self.isEffective else QAction('Activate', self)
            action.triggered.connect(self.updateAlarmState)

            menu.addAction(action)
            menu.popup(QCursor.pos())

    def updateAlarmState(self):
        listAlarm = self.module.unPickle('listAlarm')

        if listAlarm[self.name]:
            listAlarm[self.name] = False
        else:
            listAlarm[self.name] = True

        self.module.doPickle('listAlarm', listAlarm)
