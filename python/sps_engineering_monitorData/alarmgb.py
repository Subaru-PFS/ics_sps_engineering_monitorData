__author__ = 'alefur'

from functools import partial

from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QLabel, QMenu, QAction
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGridLayout, QGroupBox

from sps_engineering_Lib_dataQuery.confighandler import readState, writeState


class AlarmGB(QGroupBox):
    def __init__(self, module, alarm):
        self.module = module
        self.alarm = alarm

        if "gatevalve" in alarm.tablename:
            self.stateGatevalve = {0: "OPEN", 1: "CLOSED", 2: "UNKNOWN", 3: "INVALID"}

        QGroupBox.__init__(self)
        self.setTitle(alarm.label)

        self.grid = QGridLayout()
        self.value = QLabel()

        self.grid.addWidget(self.value, 0, 0)
        self.setLayout(self.grid)
        self.value.setStyleSheet("QLabel{font-size: 11pt; qproperty-alignment: AlignCenter; color:white;}")
        self.getValue()

    @property
    def isEffective(self):

        alarmState = readState()
        return alarmState[self.name]

    @property
    def name(self):
        return self.alarm.label.lower()

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
        dataFrame = self.module.mainWindow.db.last(self.alarm.tablename, self.alarm.key)

        try:
            val = dataFrame[self.alarm.key]
            if self.isEffective:
                if not (float(self.alarm.lbound) <= val < float(self.alarm.ubound)):
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
            activate = not self.isEffective
            action.triggered.connect(partial(self.updateAlarmState, activate))

            menu.addAction(action)
            menu.popup(QCursor.pos())

    def updateAlarmState(self, activate):
        alarmState = readState()

        if activate:
            alarmState[self.name] = True
        else:
            alarmState[self.name] = False

        writeState(alarmState)
