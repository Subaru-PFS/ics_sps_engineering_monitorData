import datetime
from functools import partial

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QGridLayout, QGroupBox, QLabel, QLineEdit


class myGroupBox(QGroupBox):
    def __init__(self, parent, tableName, deviceName, keys, labels):
        super(myGroupBox, self).__init__()

        self.timeoutlimit = 90

        self.parent = parent
        self.setStyleSheet("QGroupBox { padding-top: 20 px;border: 1px solid gray; border-radius: 3px}")
        self.setFlat(True)
        self.dict_label = {}
        self.grid = QGridLayout()
        self.format = []
        self.setLayout(self.grid)
        self.prev_date = 0
        self.prev_time = datetime.datetime.now()

        self.watcher_data = QTimer(self)
        self.watcher_data.setInterval(1500)
        self.watcher_data.timeout.connect(partial(self.waitforData, tableName, deviceName, keys))
        self.watcher_data.start()

        for i, (labs, keys) in enumerate(zip(labels, keys)):
            self.grid.addWidget(QLabel(labs.strip()), i, 0)
            label_value = QLineEdit("")
            self.setColorLine(label_value, "white")
            self.grid.addWidget(label_value, i, 1)
            self.dict_label[keys] = label_value

    def waitforData(self, tableName, deviceName, keys):
        req = "%s" % ",".join([key for key in keys])
        date, val = self.parent.db.getLastData(tableName, req)
        if date in [-1, -2, -3, -4]:
            self.parent.showError(date)
            self.watcher_data.stop()
        elif date is -5:
            self.parent.networkError = True
        else:
            self.parent.networkError = False
            self.setTitle(deviceName.capitalize() + "    " + date)
            if tableName in self.parent.alarm_widget.list_timeout:
                self.setStyleSheet(
                        "QGroupBox { padding-top: 20 px;border: 1px solid gray; border-radius: 3px;background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop:0 rgba(255,255,255, 90%), stop:1 rgba(0,0,0, 85%));}")
            else:
                self.setStyleSheet("QGroupBox { padding-top: 20 px;border: 1px solid gray; border-radius: 3px}")

            for i, key in enumerate(keys):
                if not len(str(val[i]))>8:
                    self.dict_label[key].setText(str(val[i]))
                else:
                    self.dict_label[key].setText("%.5e" % val[i])

                if self.parent.low_bound[tableName + key] <= val[i] < self.parent.high_bound[tableName + key]:
                    self.setColorLine(self.dict_label[key], "green")
                else:
                    self.setColorLine(self.dict_label[key], "red")
            if "gatevalve" in tableName:
                enum = {0 : "OPENED", 1 : "CLOSED", 2 : "UNKNOWN", 3: "INVALID"}
                self.dict_label[keys[0]].setText(enum[val[0]])

    def setColorLine(self, label, back_color):
        if back_color == "green":
            label.setStyleSheet(
                "QLineEdit { color : white; background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.5, fy:0.5, stop:0 rgba(5,145,0, 85%), stop:1 rgba(0,185,0, 85%));border-radius: 9px; qproperty-alignment: AlignCenter; font: 13pt;}")
        elif back_color == "red":
            label.setStyleSheet(
                "QLineEdit { color : white; background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.5, fy:0.5, stop:0 rgba(210,0,0, 90%), stop:1 rgba(255,0,0, 90%));border-radius: 9px; qproperty-alignment: AlignCenter; font: 13pt;}")
