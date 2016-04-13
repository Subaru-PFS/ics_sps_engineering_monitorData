from functools import partial
import datetime
import ConfigParser

from PyQt5.QtWidgets import QGridLayout, QPushButton, QLabel, QMessageBox, QWidget, QSizePolicy
from PyQt5.QtCore import QTimer, QByteArray, Qt
from PyQt5.QtGui import QMovie

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
        config.readfp(open(self.parent.os_path + "/config/alarm.cfg"))
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
        self.movie_screen.setFixedSize(80,50)

        # Add the QMovie object to the label
        self.movie.setCacheMode(QMovie.CacheAll)
        self.movie.setSpeed(100)
        self.movie_screen.setMovie(self.movie)
        self.movie.start()

        self.label_acq = QLabel("ACQUISITION")
        self.alarm_layout.addWidget(self.movie_screen, 0, 0, 1, 1)
        self.alarm_layout.addWidget(self.label_acq, 0, 1, 1, 2)
        self.setColor("QLabel", self.label_acq, "green")

        for i, device in enumerate(self.list_alarm):
            name = device["tableName"] + device["key"]
            button = QPushButton(device["label"].upper())
            button.setFixedHeight(50)
            self.setColor("QPushButton", button, "green")
            button.clicked.connect(partial(self.showWarning, "msg_%s" % name))
            self.alarm_layout.addWidget(button, 0, i + 3, 1, 1)
            setattr(self, "alarm_%s" % name, button)

        self.watcher_alarm = QTimer(self)
        self.watcher_alarm.setInterval(5000)
        self.watcher_alarm.timeout.connect(self.checkCriticalValue)
        self.watcher_alarm.start()

    def getTimeout(self):
        self.timeout_limit = 90
        self.list_timeout = []
        self.last_date = {}
        self.last_time = {}
        for key, value in self.parent.device_dict.iteritems():
            self.last_date[key] = 0
            self.last_time[key] = datetime.datetime.now()

    def getTimer(self):

        watcher_timeout = QTimer(self)
        watcher_timeout.singleShot(2000, partial(self.showTimeout, 0))
        self.checker_timeout = QTimer(self)
        self.checker_timeout.setInterval(15000)
        self.checker_timeout.timeout.connect(self.checkTimeout)
        self.checker_timeout.start()

    def showTimeout(self, i):
        if not self.networkError:
            if self.list_timeout:
                if i < len(self.list_timeout):
                    self.label_acq.setText("TIME OUT ON %s" % self.list_timeout[i])
                    self.setColor("QLabel", self.label_acq, "red")
                    i += 1
                else:
                    i = 0
            else:
                self.label_acq.setText("ACQUISITION")
                self.setColor("QLabel", self.label_acq, "green")
        else:
            self.label_acq.setText("SERVER LOST")
            self.setColor("QLabel", self.label_acq, "orange")
        watcher_timeout = QTimer(self)
        watcher_timeout.singleShot(2000, partial(self.showTimeout, i))

    def checkTimeout(self):
        for key, value in self.parent.device_dict.iteritems():
            date, id = self.parent.db.getLastData(key, "id")
            if type(id) is list:
                self.networkError = False
                id = id[0]
                if date != self.last_date[key]:
                    self.last_time[key] = datetime.datetime.now()
                    self.last_date[key] = date
                    if key in self.list_timeout:
                        self.list_timeout.remove(key)
                else:
                    if (datetime.datetime.now() - self.last_time[key]).total_seconds() > self.timeout_limit:
                        if key not in self.list_timeout:
                            self.list_timeout.append(key)
            else:
                if date not in [-1, -2, -3, -4]:
                    self.networkError = True
                else:
                    self.parent.showError(date)

    def checkCriticalValue(self):

        for device in self.list_alarm:
            name = device["tableName"] + device["key"]
            date, val = self.parent.db.getLastData(device["tableName"], device["key"])

            if type(val) is list:
                val = val[0]
                fmt = "{:.5e}" if len(str(val))>8 else "{:.2f}"
                if float(device["lower_bound"]) <= val < float(device["higher_bound"]):
                    msg = "%s OK \r %s <= %s < %s" % (
                        device["label"], device["lower_bound"], fmt.format(val), device["higher_bound"])
                    self.setColor("QPushButton", getattr(self, "alarm_%s"%name), "green")
                else:
                    msg = "WARNING ! %s OUT OF RANGE \r %s <= %s < %s" % (
                        device["label"], device["lower_bound"], fmt.format(val), device["higher_bound"])
                    self.setColor("QPushButton", getattr(self, "alarm_%s"%name), "red")
                setattr(self, "msg_%s" % name, msg)

            else:
                print "code error : %i" % val

    def setColor(self, type, widget, color):
        if type == "QLabel":
            widget.setStyleSheet(
                "%s { background-color : %s; color : white; qproperty-alignment: AlignCenter; font: 15pt;}" % (
                    type, color))
        else:
            widget.setStyleSheet("%s { background-color : %s; color : white; font: 15pt;}" % (type, color))

    def showWarning(self, attr):
        reply = QMessageBox.warning(self, 'Message', str(getattr(self, attr)), QMessageBox.Ok)
