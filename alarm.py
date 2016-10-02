import ConfigParser
import datetime
import numpy as np
from functools import partial

from PyQt5.QtCore import QTimer, QByteArray
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QGridLayout, QPushButton, QLabel, QMessageBox, QWidget, QDialog, QVBoxLayout, QCheckBox, \
    QDialogButtonBox


class alarmChecker(QWidget):
    def __init__(self, parent):
        super(alarmChecker, self).__init__()
        self.parent = parent
        self.networkError = False

        self.loadAlarm()
        self.getAlarm()
        self.getTimeout()
        self.getTimer()
        self.setLayout(self.alarm_layout)

    def loadAlarm(self):
        self.list_alarm = []
        config = ConfigParser.ConfigParser()
        config.readfp(open(self.parent.config_path + 'alarm.cfg'))
        for a in config.sections():
            dict = {"tableName": a}
            for b in config.options(a):
                dict[b] = config.get(a, b)
            self.list_alarm.append(dict)

    def getAlarm(self):

        self.alarm_layout = QGridLayout()
        self.movie = QMovie(self.parent.os_path + "/img/giphy2.gif", QByteArray(), self)

        self.movie_screen = QLabel()
        # Make label fit the gif
        self.movie_screen.setFixedSize(80, 50)

        # Add the QMovie object to the label
        self.movie.setCacheMode(QMovie.CacheAll)
        self.movie.setSpeed(100)
        self.movie_screen.setMovie(self.movie)
        self.movie.start()
        self.timeout_ack = []
        self.dialog = self.dialogTimeout()
        self.dialog.hide()

        self.label_acq = QPushButton("ACQUISITION")
        self.label_acq.clicked.connect(self.dialog.show)
        self.label_acq.setFixedHeight(50)
        self.alarm_layout.addWidget(self.movie_screen, 0, 0, 1, 1)
        self.alarm_layout.addWidget(self.label_acq, 0, 1, 1, 2)
        self.setColor("QPushButton", self.label_acq, "green")

        for i, device in enumerate(self.list_alarm):
            name = device["tableName"] + device["key"]
            button = QPushButton(device["label"].upper())
            button.setFixedHeight(50)
            self.setColor("QPushButton", button, "green")
            button.clicked.connect(partial(self.showWarning, "msg_%s" % name))
            self.alarm_layout.addWidget(button, 0, i + 3, 1, 1)
            setattr(self, "alarm_%s" % name, button)

        self.watcher_alarm = QTimer(self)
        self.watcher_alarm.setInterval(10000)
        self.watcher_alarm.timeout.connect(self.checkValueTimeout)
        self.watcher_alarm.start()

    def getTimeout(self):
        self.timeout_limit = 90
        self.list_timeout = [key for key, value in self.parent.device_dict.iteritems()]
        self.last_date = {}
        self.last_time = {}
        for key, value in self.parent.device_dict.iteritems():
            self.last_date[key] = 0
            self.last_time[key] = datetime.datetime.now()

    def checkValueTimeout(self):
        self.checkCriticalValue()
        self.checkTimeout()
        self.parent.updateGroupBox()

    def getTimer(self, i=0):

        watcher_timeout = QTimer(self)
        watcher_timeout.singleShot(3000, partial(self.showTimeout, i))

    def showTimeout(self, i):
        for timeout in self.timeout_ack:
            try:
                self.list_timeout.remove(timeout)
            except ValueError:
                pass
        if not self.networkError:
            if self.list_timeout:
                if i < len(self.list_timeout):
                    self.label_acq.setText("TIME OUT ON %s" % self.list_timeout[i])
                    self.setColor("QPushButton", self.label_acq, "red")
                    i += 1
                else:
                    i = 0
            else:
                self.label_acq.setText("ACQUISITION")
                self.setColor("QPushButton", self.label_acq, "green")
        else:
            self.label_acq.setText("SERVER LOST")
            self.setColor("QPushButton", self.label_acq, "orange")
        self.getTimer(i)

    def checkTimeout(self):
        for key, value in self.parent.device_dict.iteritems():
            return_values = self.parent.db.getLastData(key, "id")
            if return_values == -5:
                self.networkError = True
            elif type(return_values) is int:
                self.parent.showError(return_values)
            else:
                date, id = return_values
                self.networkError = False

                if date != self.last_date[key]:
                    if self.last_date[key] != 0:
                        if key in self.list_timeout:
                            self.list_timeout.remove(key)
                    self.last_time[key] = datetime.datetime.now()
                    self.last_date[key] = date
                else:
                    if (datetime.datetime.now() - self.last_time[key]).total_seconds() > self.timeout_limit:
                        if key not in self.list_timeout:
                            self.list_timeout.append(key)

    def checkCriticalValue(self):

        for device in self.list_alarm:
            name = device["tableName"] + device["key"]
            return_values = self.parent.db.getLastData(device["tableName"], device["key"])
            if type(return_values) is not int:
                date, [val] = return_values
                fmt = "{:.5e}" if len(str(val)) > 8 else "{:.2f}"
                if float(device["lower_bound"]) <= val < float(device["higher_bound"]):
                    msg = "%s OK \r %s <= %s < %s" % (
                        device["label"], device["lower_bound"], fmt.format(val), device["higher_bound"])
                    self.setColor("QPushButton", getattr(self, "alarm_%s" % name), "green")
                else:
                    msg = "WARNING ! %s OUT OF RANGE \r %s <= %s < %s" % (
                        device["label"], device["lower_bound"], fmt.format(val), device["higher_bound"])
                    self.setColor("QPushButton", getattr(self, "alarm_%s" % name), "red")
                setattr(self, "msg_%s" % name, msg)

            else:
                print "code error : %i" % return_values

    def setColor(self, type, widget, color):
        if type == "QLabel":
            widget.setStyleSheet(
                "%s { background-color : %s; color : white; qproperty-alignment: AlignCenter; font: 15pt;}" % (
                    type, color))
        else:
            widget.setStyleSheet("%s { background-color : %s; color : white; font: 15pt;}" % (type, color))

    def dialogTimeout(self):
        d = QDialog(self)
        d.setFixedWidth(450)
        d.setWindowTitle("Setting Devices Timeout")
        d.setVisible(True)
        vbox = QVBoxLayout()
        grid = QGridLayout()
        grid.setSpacing(20)

        for i, (key, value) in enumerate(self.parent.device_dict.iteritems()):
            checkbox = QCheckBox(key)
            checkbox.stateChanged.connect(partial(self.ackTimeout, checkbox))
            checkbox.setCheckState(2)
            grid.addWidget(checkbox, 1 + i, 0, 1, 3)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.button(QDialogButtonBox.Ok).clicked.connect(d.hide)
        buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(d.hide)
        vbox.addLayout(grid)
        vbox.addWidget(buttonBox)
        d.setLayout(vbox)
        return d

    def ackTimeout(self, checkbox):
        if checkbox.isChecked():
            if str(checkbox.text()) in self.timeout_ack:
                self.timeout_ack.remove(str(checkbox.text()))
        else:
            self.timeout_ack.append(str(checkbox.text()))

    def showWarning(self, attr):
        reply = QMessageBox.warning(self, 'Message', str(getattr(self, attr)), QMessageBox.Ok)
