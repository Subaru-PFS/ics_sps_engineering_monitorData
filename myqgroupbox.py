import datetime

from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QGridLayout, QGroupBox, QLabel, QLineEdit, QApplication, QPushButton


class EyeButton(QPushButton):
    def __init__(self, module):
        QPushButton.__init__(self)
        self.module = module
        self.setParent(module)
        eyeOn = QPixmap()
        eyeOff = QPixmap()

        eyeOn.load(module.mainWindow.imgPath + 'eye_on.png')
        eyeOff.load(module.mainWindow.imgPath + 'eye_off.png')
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


class AlarmGB(QGroupBox):
    def __init__(self, module, alarm):
        self.module = module
        self.alarm = alarm

        if "gatevalve" in alarm["tablename"]:
            self.stateGatevalve = {0: "OPENED", 1: "CLOSED", 2: "UNKNOWN", 3: "INVALID"}

        QGroupBox.__init__(self)
        self.setTitle(alarm["label"])

        self.grid = QGridLayout()
        self.value = QLabel()

        self.grid.addWidget(self.value, 0, 0)
        self.setLayout(self.grid)
        self.value.setStyleSheet("QLabel{font-size: 11pt; qproperty-alignment: AlignCenter; color:white;}")

    @property
    def isEffective(self):

        listAlarm = self.module.unPickle('listAlarm')
        return listAlarm[self.alarm["label"].lower()]

    def setColor(self, color):
        if color == "red":
            self.setStyleSheet(
                "QGroupBox {font-size: 9pt; background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #f43131, stop: 1 #5e1414);border: 1px solid gray;border-radius: 3px;margin-top: 1ex;} " +
                "QGroupBox::title {subcontrol-origin: margin;subcontrol-position: top center; padding: 0 3px;}")
        elif color == "green":
            self.setStyleSheet(
                "QGroupBox {font-size: 9pt; background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #45f42e, stop: 1 #195511);border: 1px solid gray;border-radius: 3px;margin-top: 1ex;} " +
                "QGroupBox::title {subcontrol-origin: margin;subcontrol-position: top center; padding: 0 3px;}")

    def getValue(self):
        return_values = self.module.mainWindow.db.getLastData(self.alarm["tablename"], self.alarm["key"])

        if return_values == -5:
            self.module.acquisition.networkError = True
        elif type(return_values) is int:
            self.module.mainWindow.showError(return_values)
            self.module.timerData.stop()
        else:
            self.module.acquisition.networkError = False
            date, val = return_values

            if not hasattr(self, "stateGatevalve"):
                val = val[0]
                fmt = "{:.3e}" if len(str(val)) > 7 else "{:.2f}"
                self.value.setText(fmt.format(val))
            else:
                self.value.setText(self.stateGatevalve[val[0]])

            if self.isEffective and not (float(self.alarm["lower_bound"]) <= val < float(self.alarm["higher_bound"])):
                self.setColor("red")
            else:
                self.setColor("green")

class DeviceGB(QGroupBox):
    def __init__(self, module, tableName, deviceName, keys, labels, units, lowBounds, upBounds):
        QGroupBox.__init__(self)

        self.timeoutlimit = 90

        self.module = module
        self.tableName = tableName
        self.deviceName = deviceName
        self.keys = keys
        self.labels = labels
        self.units = units
        self.lowBounds = lowBounds
        self.upBounds = upBounds

        self.formats = ["{:.2e}" if uni.strip() in ['Torr', 'mBar', 'Bar'] else '{:.2f}' for uni in units]
        self.sqlRequest = "%s" % ",".join([key for key in self.keys])

        if "gatevalve" in self.tableName:
            self.stateGatevalve = {0: "OPENED", 1: "CLOSED", 2: "UNKNOWN", 3: "INVALID"}

        self.setFlat(True)
        self.dict_label = {}
        self.grid = QGridLayout()

        self.setLayout(self.grid)
        self.prev_date = 0
        self.prev_time = datetime.datetime.now()

        devName = DeviceName(self, deviceName.capitalize())

        self.grid.addWidget(devName, 0, 0)

        for i, (lab, key, unit) in enumerate(zip(labels, keys, units)):
            labelName = self.getLabelName(lab, unit)
            labelValue = self.getLabelValue(key)
            self.grid.addWidget(labelName, 3 * i + 1, 0, 3, 1)
            self.grid.addWidget(labelValue, 3 * i + 1, 1, 3, 1)

        self.grid.setSpacing(2.)
        self.setOffline()

    def waitforData(self):

        return_values = self.module.mainWindow.db.getLastData(self.tableName, self.sqlRequest)
        if return_values == -5:
            self.module.acquisition.networkError = True
        elif type(return_values) is int:
            self.module.mainWindow.showError(return_values)
            self.module.timerData.stop()
        else:
            self.module.acquisition.networkError = False
            date, val = return_values

            self.setTitle(date)

            for i, (key, fmt, lowBound, upBound) in enumerate(
                    zip(self.keys, self.formats, self.lowBounds, self.upBounds)):
                try:
                    self.setNewValue(self.dict_label[key], fmt.format(val[i]))
                    if self.tableName not in self.module.acquisition.vistimeout:
                        if float(lowBound) <= val[i] < float(upBound):
                            self.setColorLine(self.dict_label[key], "green")
                        else:
                            self.setColorLine(self.dict_label[key], "red")
                except ValueError:
                    print "fmt=", fmt
                    print "val=", val

            if hasattr(self, "stateGatevalve"):
                self.dict_label[self.keys[0]].setText(self.stateGatevalve[val[0]])

    def setColorLine(self, label, back_color):
        if back_color == "green":
            label.setStyleSheet(
                "QLineEdit { color : white; background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.5, fy:0.5, stop:0 rgba(5,145,0, 85%), stop:1 rgba(0,185,0, 85%));border-radius: 6px; qproperty-alignment: AlignCenter; font-size: 9pt;}")
        elif back_color == "red":
            label.setStyleSheet(
                "QLineEdit { color : white; background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.5, fy:0.5, stop:0 rgba(210,0,0, 90%), stop:1 rgba(255,0,0, 90%));border-radius: 6px; qproperty-alignment: AlignCenter; font-size: 9pt;}")
        elif back_color == "black":
            label.setStyleSheet(
                "QLineEdit { color : white; background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.5, fy:0.5, stop:0 rgba(40,40,40, 90%), stop:1 rgba(0,0,0, 90%));border-radius: 6px; qproperty-alignment: AlignCenter; font-size: 9pt;}")

    def getLabelName(self, labs, unit):
        label = QLabel("    %s (%s)" % (labs.strip().title(), unit.strip()))
        label.setStyleSheet("QLabel{font-size: 8pt;}")

        return label

    def getLabelValue(self, keys):
        label_value = QLineEdit("")
        self.setColorLine(label_value, "white")
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
            self.setColorLine(self.dict_label[key], "black")
        self.setStyleSheet(
            "QGroupBox {font-size:12px; background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop:0 rgba(255,255,255, 90%), stop:1 rgba(0,0,0, 85%));border: 2px solid gray;border-radius: 5px;} QGroupBox::title {subcontrol-origin: margin;subcontrol-position: top right; padding: 0 3px;}")
