import datetime
from functools import partial

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QGridLayout, QGroupBox, QLabel, QLineEdit


class myGroupBox(QGroupBox):
    def __init__(self, parent, tableName, deviceName, keywords, labels):
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
        self.watcher_data.timeout.connect(partial(self.waitforData, tableName, deviceName, keywords))
        self.watcher_data.start()

        for i, (labs, keys) in enumerate(zip(labels, keywords)):
            self.grid.addWidget(QLabel(labs), i, 0)
            if "pressure" in labs.lower():
                self.format.append(True)
            else:
                self.format.append(False)
            label_value = QLineEdit("")
            self.setColorLine(label_value, "white", "black")
            self.grid.addWidget(label_value, i, 1)
            self.dict_label[keys] = label_value

    def waitforData(self, tableName, deviceName, keywords):
        req = "%s" % ",".join([keys for keys in keywords])
        date, val = self.parent.database.getLastData(tableName, req)
        if (date, val) == (-2, -2) or (date, val) == (-3, -3):
            self.parent.showError(date)
            self.watcher_data.stop()
        else:
            self.setTitle(deviceName.capitalize() + "    " + date)

        for i, keys in enumerate(keywords):
            if not self.format[i]:
                self.dict_label[keys].setText(str(val[i]))
            else:
                self.dict_label[keys].setText("%.5e" % val[i])

            if self.parent.low_bound[tableName + keys] < val[i] <= self.parent.high_bound[tableName + keys]:
                self.setColorLine(self.dict_label[keys], "green")
            else:
                self.setColorLine(self.dict_label[keys], "red")
        if date == self.prev_date:
            delta = (datetime.datetime.now() - self.prev_time).total_seconds()
            if delta > self.timeoutlimit:
                if tableName not in self.parent.list_timeout:
                    self.parent.list_timeout.append(tableName)
                    self.setStyleSheet(
                        "QGroupBox { padding-top: 20 px;border: 1px solid gray; border-radius: 3px;background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop:0 rgba(255,255,255, 90%), stop:1 rgba(0,0,0, 85%));}")
            else:
                if tableName in self.parent.list_timeout:
                    self.parent.list_timeout.remove(tableName)
                    self.setStyleSheet("QGroupBox { padding-top: 20 px;border: 1px solid gray; border-radius: 3px}")
        else:
            self.prev_date = date
            self.prev_time = datetime.datetime.now()

        if tableName == "xcu_r1__gatevalve":
            if val[0] == 253:
                self.dict_label["val1"].setText("OPENED")
            else:
                self.dict_label["val1"].setText("CLOSED")

    def setColorLine(self, label, back_color, color="white"):
        if back_color == "green":
            label.setStyleSheet(
                "QLineEdit { color : white; background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.5, fy:0.5, stop:0 rgba(5,145,0, 85%), stop:1 rgba(0,185,0, 85%));border-radius: 9px; qproperty-alignment: AlignCenter; font: 13pt;}")
        elif back_color == "red":
            label.setStyleSheet(
                "QLineEdit { color : white; background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.5, fy:0.5, stop:0 rgba(210,0,0, 90%), stop:1 rgba(255,0,0, 90%));border-radius: 9px; qproperty-alignment: AlignCenter; font: 13pt;}")
