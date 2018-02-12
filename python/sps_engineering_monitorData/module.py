import os
from functools import partial
from collections import OrderedDict

import psycopg2

from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QGroupBox, QMenu, QAction,QPushButton
from PyQt5.QtGui import QPixmap, QIcon, QCursor
from PyQt5.QtCore import Qt

from devicegb import DeviceGB
from acquisition import Acquisition
from alarmgb import AlarmGB

from sps_engineering_Lib_dataQuery.confighandler import readMode, writeMode


class Module(QGroupBox):
    def __init__(self, mainWindow, name, devices):
        QGroupBox.__init__(self)

        self.mainWindow = mainWindow
        self.name = name
        self.devices = devices

        self.path = '%s/alarm/' % self.mainWindow.configPath

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

    @property
    def actors(self):
        return list(OrderedDict.fromkeys([device.tablename.split('__')[0] for device in self.devices]))

    @property
    def isOffline(self):
        return True if self.mode == 'offline' else False

    def initialize(self):
        self.createGroupBox()

        self.eyeButton = EyeButton(self)
        self.acquisition = Acquisition(self)

        self.alarmLayout.addWidget(self.acquisition)

    def setAlarms(self, alarms):
        hide = self.cleanAlarms()
        self.mode = alarms[0].mode if alarms else 'offline'
        self.setTitle('%s - %s ' % (self.name, self.mode))

        for alarm in alarms:
            widget = AlarmGB(self, alarm)
            self.alarmGB.append(widget)
            self.alarmLayout.addWidget(widget)
            widget.hide() if hide else widget.show()

    def cleanAlarms(self):
        hide = False
        while self.alarmGB:
            alarm = self.alarmGB[0]
            hide = alarm.isHidden()
            self.alarmLayout.removeWidget(alarm)
            alarm.deleteLater()
            self.alarmGB.remove(alarm)

        return hide

    def moveEye(self):

        try:
            self.eyeButton.move(self.width() - 30, 0)
        except:
            pass

    def createGroupBox(self):
        for i, deviceConf in enumerate(self.devices):
            self.groupBox.append(DeviceGB(self, deviceConf))
            self.gbLayout.addWidget(self.groupBox[-1], (i // self.divcoeff) + 1, i % self.divcoeff)

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
            self.setMaximumHeight(800)
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
        try:
            for groupbox in self.groupBox:
                groupbox.waitforData()
            for alarm in self.alarmGB:
                alarm.getValue()
            self.acquisition.network = True

        except psycopg2.OperationalError:
            self.acquisition.network = False
            self.mainWindow.db.close()

    def updateMode(self, mode):
        modes = readMode()
        for actor in self.actors:
            modes[actor] = mode

        writeMode(modes)

    def getGroupBox(self, tableName):
        for i, device in enumerate(self.devices):
            if device.tablename == tableName:
                return self.groupBox[i]

    def mouseReleaseEvent(self, QMouseEvent):
        if QMouseEvent.button() == Qt.RightButton:
            menu = QMenu(self)

            all_modes = [f[:-4] for f in next(os.walk(self.path))[-1] if '.cfg' in f]
            for mode in all_modes:
                action = QAction(mode, self)
                action.triggered.connect(partial(self.updateMode, mode))
                menu.addAction(action)

            menu.popup(QCursor.pos())

    def resizeEvent(self, QResizeEvent):
        self.moveEye()
        QGroupBox.resizeEvent(self, QResizeEvent)


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
