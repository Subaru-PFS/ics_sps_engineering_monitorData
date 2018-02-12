__author__ = 'alefur'
import datetime

from PyQt5.QtWidgets import QLineEdit, QApplication
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QGridLayout, QGroupBox


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
            self.groupbox.deviceName, '!!'.join(labs), self.groupbox.title(), '||'.join(vals))

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

        if "gatevalve" in self.tablename:
            self.stateGatevalve = {0: "OPEN", 1: "CLOSED", 2: "UNKNOWN", 3: "INVALID"}

        self.setFlat(True)
        self.dict_label = {}
        self.grid = QGridLayout()

        self.setLayout(self.grid)
        self.prev_date = 0
        self.prev_time = datetime.datetime.now()

        devName = DeviceName(self, self.deviceLabel.capitalize())

        self.grid.addWidget(devName, 0, 0)
        for i, (lab, key, unit) in enumerate(zip(self.labels, self.keys, self.units)):
            qLabelName = self.getLabelName(lab, unit)
            qlabelValue = self.getLabelValue(key)
            self.grid.addWidget(qLabelName, 3 * i + 1, 0, 3, 1)
            self.grid.addWidget(qlabelValue, 3 * i + 1, 1, 3, 1)

        self.grid.setSpacing(1.)
        self.setOffline()

    def waitforData(self):

        dataFrame = self.module.mainWindow.db.last(self.tablename, self.sqlRequest)

        self.module.acquisition.checkTimeout(self.tablename, dataFrame['tai'])
        self.setTitle(dataFrame.strdate)

        for (key, fmt, lowBound, upBound) in (zip(self.keys, self.formats, self.lbounds, self.ubounds)):
            labelWidget = self.dict_label[key]
            try:
                value = dataFrame[key]

                if float(lowBound) <= value < float(upBound):
                    self.colorLabel(self.dict_label[key], "green")
                else:
                    self.colorLabel(self.dict_label[key], "red")

                valueStr = fmt.format(value)
            except (ValueError, TypeError):
                valueStr = 'nan'

            self.setNewValue(labelWidget, valueStr)

        if hasattr(self, "stateGatevalve"):
            self.dict_label[self.keys[0]].setText(self.stateGatevalve[int(dataFrame['position'])])

    def getLabelName(self, labs, unit):
        label = QLabel("    %s (%s)" % (labs.strip().title(), unit.strip()))
        label.setStyleSheet("QLabel{font-size: 8pt;}")

        return label

    def getLabelValue(self, keys):
        label_value = QLineEdit("")
        self.colorLabel(label_value, "white")
        self.dict_label[keys] = label_value

        return label_value

    def setNewValue(self, label, valStr):

        label.setText(valStr)
        label.setMinimumWidth(9 * len(valStr))

    def setOnline(self):
        self.setStyleSheet(
            "QGroupBox {font-size:12px; background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #E0E0E0, stop: 1 #FFFFFF);border: 2px solid gray;border-radius: 5px;} QGroupBox::title {subcontrol-origin: margin;subcontrol-position: top right; padding: 0 3px;}")

    def setOffline(self):
        for key in self.keys:
            self.colorLabel(self.dict_label[key], "black")
        self.setStyleSheet(
            "QGroupBox {font-size:12px; background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop:0 rgba(255,255,255, 90%), stop:1 rgba(0,0,0, 85%));border: 2px solid gray;border-radius: 5px;} QGroupBox::title {subcontrol-origin: margin;subcontrol-position: top right; padding: 0 3px;}")

    def colorLabel(self, label, back_color):
        if back_color == "green":
            label.setStyleSheet(
                "QLineEdit { color : white; background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.5, fy:0.5, stop:0 rgba(5,145,0, 85%), stop:1 rgba(0,185,0, 85%));border-radius: 6px; qproperty-alignment: AlignCenter; font-size: 9pt;}")
        elif back_color == "red":
            label.setStyleSheet(
                "QLineEdit { color : white; background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.5, fy:0.5, stop:0 rgba(210,0,0, 90%), stop:1 rgba(255,0,0, 90%));border-radius: 6px; qproperty-alignment: AlignCenter; font-size: 9pt;}")
        elif back_color == "black":
            label.setStyleSheet(
                "QLineEdit { color : white; background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.5, fy:0.5, stop:0 rgba(40,40,40, 90%), stop:1 rgba(0,0,0, 90%));border-radius: 6px; qproperty-alignment: AlignCenter; font-size: 9pt;}")