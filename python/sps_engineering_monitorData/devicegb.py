__author__ = 'alefur'
import datetime

from PyQt5.QtWidgets import QLineEdit, QApplication
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QGridLayout, QGroupBox


class LabelValue(QLineEdit):
    def __init__(self, fmt, lbound, ubound, GvState):
        QLineEdit.__init__(self, "")
        self.fmt = fmt
        self.lbound = lbound
        self.ubound = ubound
        self.GvState = GvState
        self.colorLabel("white")

    def setNewValue(self, value):

        try:
            if float(self.lbound) <= value < float(self.ubound):
                self.colorLabel("green")
            else:
                self.colorLabel("red")

            valueStr = self.fmt.format(value) if not self.GvState else self.GvState[value]

        except (ValueError, TypeError):
            valueStr = 'nan'

        self.setText(valueStr)


    def colorLabel(self, back_color):
        if back_color == "green":
            self.setStyleSheet(
                "QLineEdit { color : white; background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.5, fy:0.5, stop:0 rgba(5,145,0, 85%), stop:1 rgba(0,185,0, 85%));border-radius: 6px; qproperty-alignment: AlignCenter; font-size: 9pt;}")
        elif back_color == "red":
            self.setStyleSheet(
                "QLineEdit { color : white; background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.5, fy:0.5, stop:0 rgba(210,0,0, 90%), stop:1 rgba(255,0,0, 90%));border-radius: 6px; qproperty-alignment: AlignCenter; font-size: 9pt;}")
        elif back_color == "black":
            self.setStyleSheet(
                "QLineEdit { color : white; background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.5, fy:0.5, stop:0 rgba(40,40,40, 90%), stop:1 rgba(0,0,0, 90%));border-radius: 6px; qproperty-alignment: AlignCenter; font-size: 9pt;}")



class LabelName(QLabel):
    def __init__(self, labs, unit):
        QLabel.__init__(self, "    %s (%s)" % (labs.strip().title(), unit.strip()))
        self.setStyleSheet("QLabel{font-size: 8pt;}")


class DeviceName(QLabel):
    def __init__(self, groupbox, name):
        QLabel.__init__(self, name)

        self.groupbox = groupbox
        self.setStyleSheet("QLabel{font-weight:bold; font-size: 10pt;}")

    def mouseDoubleClickEvent(self, QMouseEvent):
        labs = []
        vals = []
        for lab, key in zip(self.groupbox.labels, self.groupbox.keys):
            labs.append(lab)
            vals.append(self.groupbox.dict_label[key].text())

        cp = '{| class="wikitable" \n|- \n!%s !! %s \n|- \n| %s || %s \n|}' % (
            self.groupbox.deviceLabel, '!!'.join(labs), self.groupbox.title(), '||'.join(vals))

        pressPaper = QApplication.clipboard()
        pressPaper.setText(cp)


class DeviceGB(QGroupBox):
    def __init__(self, module, deviceConf):
        QGroupBox.__init__(self)

        self.timeoutlimit = 90

        self.module = module
        self.tablename = deviceConf.tablename
        self.deviceLabel = deviceConf.deviceLabel
        self.keys = deviceConf.keys
        self.labels = deviceConf.labels
        self.units = deviceConf.units
        self.lbounds = deviceConf.lbounds
        self.ubounds = deviceConf.ubounds

        self.formats = ["{:g}" for uni in self.units]
        self.sqlRequest = "%s" % ",".join([key for key in self.keys])

        GvState = {0: "OPEN", 1: "CLOSED", 2: "UNKNOWN", 3: "INVALID"} if "gatevalve" in self.tablename else False

        self.setFlat(True)
        self.dict_label = {}
        self.grid = QGridLayout()

        self.setLayout(self.grid)
        self.prev_date = 0
        self.prev_time = datetime.datetime.now()

        devName = DeviceName(self, self.deviceLabel.capitalize())
        self.grid.addWidget(devName, 0, 0)

        for i in range(len(self.labels)):

            labelName = LabelName(self.labels[i], self.units[i])
            labelValue = LabelValue(self.formats[i], self.lbounds[i], self.ubounds[i], GvState)

            self.grid.addWidget(labelName, 3 * i + 1, 0, 3, 1)
            self.grid.addWidget(labelValue, 3 * i + 1, 1, 3, 1)

            self.dict_label[self.keys[i]] = labelValue

        self.grid.setSpacing(1)

        self.setOffline()

    def waitforData(self):

        dataFrame = self.module.mainWindow.db.last(self.tablename, self.sqlRequest)

        self.module.acquisition.checkTimeout(self.tablename, dataFrame['tai'])
        self.setTitle(dataFrame.strdate)

        for key in self.keys:
             labelWidget = self.dict_label[key]

             value = dataFrame[key]
             labelWidget.setNewValue(value)

    #
    def setOnline(self):
        self.setStyleSheet(
            "QGroupBox {font-size:12px; background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #E0E0E0, stop: 1 #FFFFFF);border: 2px solid gray;border-radius: 5px;} QGroupBox::title {subcontrol-origin: margin;subcontrol-position: top right; padding: 0 3px;}")

    def setOffline(self):
        for key in self.keys:
            self.dict_label[key].colorLabel("black")
        self.setStyleSheet(
            "QGroupBox {font-size:12px; background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop:0 rgba(255,255,255, 90%), stop:1 rgba(0,0,0, 85%));border: 2px solid gray;border-radius: 5px;} QGroupBox::title {subcontrol-origin: margin;subcontrol-position: top right; padding: 0 3px;}")