import datetime
from functools import partial

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QGridLayout, QGroupBox, QLabel, QLineEdit


class myGroupBox(QGroupBox):
    def __init__(self, parent, tableName, deviceName, keys, labels, units):
        super(myGroupBox, self).__init__()

        self.timeoutlimit = 90

        self.parent = parent
        self.tableName = tableName
        self.deviceName = deviceName
        self.keys = keys
        self.labels = labels
        self.formats = ["{:.3e}" if uni.strip() in ['Torr', 'mBar', 'Bar'] else '{:.2f}' for uni in units]

        if "gatevalve" in self.tableName:
                self.stateGatevalve = {0: "OPENED", 1: "CLOSED", 2: "UNKNOWN", 3: "INVALID"}
        self.setStyleSheet("QGroupBox { padding-top: 20 px;border: 1px solid gray; border-radius: 3px}")
        self.setFlat(True)
        self.dict_label = {}
        self.grid = QGridLayout()

        self.setLayout(self.grid)
        self.prev_date = 0
        self.prev_time = datetime.datetime.now()

        self.watcher_data = QTimer(self)
        self.watcher_data.setInterval(1500)
        self.watcher_data.timeout.connect(self.waitforData)
        self.watcher_data.start()

        for i, (labs, keys, unit) in enumerate(zip(labels, keys, units)):
            self.grid.addWidget(QLabel("%s (%s)"%(labs.strip().title(), unit.strip())), i, 0)
            label_value = QLineEdit("")
            self.setColorLine(label_value, "white")
            self.grid.addWidget(label_value, i, 1)
            self.dict_label[keys] = label_value

    def waitforData(self):
        req = "%s" % ",".join([key for key in self.keys])
        return_values = self.parent.db.getLastData(self.tableName, req)
        if return_values == -5:
            self.parent.networkError = True
        elif type(return_values) is int:
            self.parent.showError(return_values)
            self.watcher_data.stop()
        else:
            date, val = return_values
            self.parent.networkError = False
            self.setTitle(self.deviceName.capitalize() + "    " + date)
            if self.tableName in self.parent.alarm_widget.list_timeout+self.parent.alarm_widget.timeout_ack:
                self.setStyleSheet(
                    "QGroupBox { padding-top: 20 px;border: 1px solid gray; border-radius: 3px;background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop:0 rgba(255,255,255, 90%), stop:1 rgba(0,0,0, 85%));}")
            else:
                self.setStyleSheet("QGroupBox { padding-top: 20 px;border: 1px solid gray; border-radius: 3px}")

            for i, (key, fmt) in enumerate(zip(self.keys, self.formats)):
                self.dict_label[key].setText(fmt.format(val[i]))
                if self.parent.low_bound[self.tableName + key] <= val[i] < self.parent.high_bound[self.tableName + key]:
                    self.setColorLine(self.dict_label[key], "green")
                else:
                    self.setColorLine(self.dict_label[key], "red")
            if hasattr(self, "stateGatevalve"):
                self.dict_label[self.keys[0]].setText(self.stateGatevalve[val[0]])

    def setColorLine(self, label, back_color):
        if back_color == "green":
            label.setStyleSheet(
                "QLineEdit { color : white; background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.5, fy:0.5, stop:0 rgba(5,145,0, 85%), stop:1 rgba(0,185,0, 85%));border-radius: 9px; qproperty-alignment: AlignCenter; font: 13pt;}")
        elif back_color == "red":
            label.setStyleSheet(
                "QLineEdit { color : white; background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.5, fy:0.5, stop:0 rgba(210,0,0, 90%), stop:1 rgba(255,0,0, 90%));border-radius: 9px; qproperty-alignment: AlignCenter; font: 13pt;}")
