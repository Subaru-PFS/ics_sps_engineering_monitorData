import pickle
import random
import time
import psycopg2

from PyQt5.QtCore import QTimer

from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QGroupBox

from myqgroupbox import DeviceGB
from summary import EyeButton, Acquisition, AlarmGB


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

        self.timerData = QTimer(self)
        self.timerData.setInterval(15000)
        self.timerData.timeout.connect(self.waitforData)
        self.timerData.start()

    def initialize(self):
        self.createGroupBox()

        self.eyeButton = EyeButton(self)
        self.acquisition = Acquisition(self)

        self.alarmLayout.addWidget(self.acquisition)

    def setAlarms(self, alarms):
        self.cleanAlarms()
        self.mode = alarms[0]['mode']
        self.setTitle('%s - %s ' % (self.name, self.mode))

        for alarm in alarms:
            self.alarmGB.append(AlarmGB(self, alarm))
            self.alarmLayout.addWidget(self.alarmGB[-1])

    def cleanAlarms(self):

        while self.alarmGB:
            alarm = self.alarmGB[0]
            self.alarmLayout.removeWidget(alarm)
            alarm.deleteLater()
            self.alarmGB.remove(alarm)

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
            upBounds = boxes["upper_bound"].split(',')

            self.groupBox.append(DeviceGB(self, tableName, deviceName, keys, labels, units, lowBounds, upBounds))
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

    def resizeEvent(self, QResizeEvent):
        self.moveEye()
        QGroupBox.resizeEvent(self, QResizeEvent)

    def getGroupBox(self, tableName):
        for i, boxes in enumerate(self.devices):
            table = boxes["tablename"]
            if table == tableName:
                return self.groupBox[i]

    def unPickle(self, filename, empty=None):

        try:
            with open(self.path + filename, 'rb') as thisFile:
                unpickler = pickle.Unpickler(thisFile)
                return unpickler.load()
        except IOError:
            print("creating empty %s file" % filename)
            var = {} if empty is None else []
            self.doPickle(filename, var)
            return var
        except EOFError:
            print("except EOFError")
            time.sleep(0.5 + 2 * random.random())
            return self.unPickle(filename=filename, empty=empty)

    def doPickle(self, filename, var):
        with open(self.path + filename, 'wb') as thisFile:
            pickler = pickle.Pickler(thisFile)
            pickler.dump(var)
