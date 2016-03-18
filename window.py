#!/usr/bin/env python
# encoding: utf-8

import ConfigParser
from functools import partial

from ics_sps_engineering_Lib_dataQuery import databaseManager
try:
    from tabulate import tabulate
    Wiki = True
except ImportError:
    Wiki = False
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QWidget, QMainWindow, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QPushButton, \
    QMessageBox, QAction, QDialog, QDialogButtonBox, QLineEdit, QCheckBox, QProgressBar, QApplication, QProgressDialog
from PyQt5.QtGui import QIcon

from myqgroupbox import myGroupBox
import datetime as dt


class mainWindow(QMainWindow):
    def __init__(self, path, ip, port):
        super(mainWindow, self).__init__()

        self.database = databaseManager(ip, port)
        self.path = path
        self.tab = []
        self.tabCsv = []
        self.low_bound = {}
        self.high_bound = {}
        self.readCfg(self.path + "/config/curve_config.cfg")
        self.initialize()
        self.getToolbar()

    def initialize(self):

        self.widget = QWidget()
        self.global_layout = QGridLayout()
        self.no_err = self.database.initDatabase()
        if self.no_err != -1:
            self.getAlarm(["pressure", "turbo", "gatevalve", "cooler"])
            self.getTimeout()
            self.getGroupBox()
        else:
            self.showError(self.no_err)

        self.menubar = self.menuBar()
        self.about_action = QAction('About', self)
        self.about_action.triggered.connect(
            partial(self.showInformation, "MonitorActor v0.3 working with Extract data v0.3"))
        self.helpMenu = self.menubar.addMenu('&?')
        self.helpMenu.addAction(self.about_action)
        self.width = 1152
        self.height = 864
        self.center = [300, 300]
        self.title = " AIT-PFS Monitoring CU"
        self.resize(self.width, self.height)
        self.move(self.center[0], self.center[1])
        self.setWindowTitle(self.title)
        self.show()

    def getToolbar(self):
        extract2csvAction = QAction(QIcon(self.path + 'img/spreadsheet.png'), 'Extract to Csv', self)
        extract2csvAction.triggered.connect(self.dialogExtract2csv)
        wikiAction = QAction(QIcon(self.path + 'img/wiki.png'), 'Copy to MediaWiki', self)
        wikiAction.triggered.connect(self.copy2wiki)
        self.toolbar = self.addToolBar('Extract to Csv')
        self.toolbar.addAction(extract2csvAction)
        self.toolbar.addAction(wikiAction)

    def dialogExtract2csv(self):
        d = QDialog(self)
        d.setFixedWidth(450)
        d.setWindowTitle("Extract data to Csv")
        d.setVisible(True)
        vbox = QVBoxLayout()
        grid = QGridLayout()
        grid.setSpacing(20)
        line_edit_begin = QLineEdit(
            dt.datetime(dt.datetime.today().year, dt.datetime.today().month, dt.datetime.today().day).strftime(
                "%d/%m/%Y %H:%M:%S"))
        line_edit_end = QLineEdit("Now")
        grid.addWidget(QLabel("From"), 0, 0)
        grid.addWidget(line_edit_begin, 0, 1)
        grid.addWidget(QLabel("To"), 0, 2)
        grid.addWidget(line_edit_end, 0, 3)
        for i, boxes in enumerate(self.tab):
            checkbox = QCheckBox(boxes[1])
            checkbox.stateChanged.connect(partial(self.csvUpdateTab, checkbox, [boxes[0], boxes[2], boxes[3]]))
            checkbox.setCheckState(2)
            grid.addWidget(checkbox, 1 + i, 0, 1, 3)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.button(QDialogButtonBox.Ok).clicked.connect(
            partial(self.extract2csv, d, line_edit_begin, line_edit_end))
        buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(d.close)
        vbox.addLayout(grid)
        vbox.addWidget(buttonBox)
        d.setLayout(vbox)

    def extract2csv(self, d, begin, end):
        fail = []
        progress = QProgressDialog("Extracting data", "Abort Extracting", 0, len(self.tabCsv)-1)
        progress.setFixedSize(300,200)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Extracting data...")
        for i, device in enumerate(self.tabCsv):
            progress.setValue(i)
            ret = self.database.extract2csv(device[0], device[1], device[2], str(begin.text()), str(end.text()))
            if ret is None :fail.append(device[0])
        if fail:
            self.showInformation("Extraction error on %s" % ','.join(fail))
        else:
            self.showInformation("Extraction Completed")
        d.close()

    def copy2wiki(self):
        if Wiki:
            config = ConfigParser.ConfigParser()
            config.readfp(open(self.path+"config/mediawiki.cfg"))
            selectdata = []
            for a in config.sections():
                selectdata.append([a])
                for b in config.options(a):
                    selectdata[-1].append(config.get(a, b))

            data_list = [["Sensor Name", "Temp. Value", "Unit", "Read by", "Type", "Cold/warm"]]
            for i, groups in enumerate(selectdata):
                tableName = groups[0]
                keywords = groups[2]
                labels = groups[3].split(',')
                typeName = groups[4]
                deviceName = groups[1]
                unitName = groups[5].split(',') if len(groups[5].split(',')) > 1 else len(labels) * [groups[5]]
                typeTemps = groups[6].split(',')
                dates, vals = self.database.getLastData(tableName, keywords)

                for (key, val, ttemp, unit) in zip(labels, vals, typeTemps, unitName):
                    data_list.append([key, val, unit, deviceName, typeName, ttemp])

            wikistr = tabulate(data_list, headers="firstrow", tablefmt="mediawiki")
            wikihead = "{| class=\"wikitable sortable centre\" style=\"text-align: left;\"" + "\n" + "|+ Temperature sensors value " + str(dates) + "\n"

            for key in data_list[0]:
                wikihead += "! scope=\"col\"|\'\'\'" + key + "\'\'\'" + "\n"
            wikiTableCode = wikihead + wikistr[206:]
            self.pressPaper = QApplication.clipboard()
            self.pressPaper.setText(wikiTableCode)


    def csvUpdateTab(self, checkbox, device):
        if checkbox.isChecked() and device not in self.tabCsv:
            self.tabCsv.append(device)
        elif not checkbox.isChecked() and device in self.tabCsv:
            self.tabCsv.remove(device)

    def readCfg(self, path):
        config = ConfigParser.ConfigParser()
        config.readfp(open(path))
        for a in config.sections():
            self.tab.append([a])
            for b in config.options(a):
                if b == "lower_bound":
                    keywords = config.get(a, "keyword").split(',')
                    minimums = config.get(a, "lower_bound").split(',')
                    maximums = config.get(a, "higher_bound").split(',')
                    for low_bound, high_bound, key in zip(minimums, maximums, keywords):
                        self.low_bound[a + key] = float(low_bound)
                        self.high_bound[a + key] = float(high_bound)
                elif b == "higher_bound":
                    pass

                else:
                    self.tab[-1].append(config.get(a, b))

    def getTimeout(self):
        self.list_timeout = []
        watcher_timeout = QTimer(self)
        watcher_timeout.singleShot(2000, partial(self.checkTimeout, 0))

    def checkTimeout(self, i):
        if self.list_timeout:
            if i < len(self.list_timeout):
                self.label_acq.setText("TIME OUT %s" % self.list_timeout[i])
                self.setColor("QLabel", self.label_acq, "red")
                i += 1
            else:
                i = 0
        else:
            self.label_acq.setText("ACQUISITION")
            self.setColor("QLabel", self.label_acq, "green")

        watcher_timeout = QTimer(self)
        watcher_timeout.singleShot(2000, partial(self.checkTimeout, i))

    def getAlarm(self, devices):

        self.alarm_layout = QGridLayout()
        self.label_acq = QLabel("ACQUISITION")
        self.alarm_layout.addWidget(self.label_acq, 0, 0, 1, 2)
        self.setColor("QLabel", self.label_acq, "green")

        for i, device in enumerate(devices):
            button = QPushButton(device.upper())
            self.setColor("QPushButton", button, "green")
            button.clicked.connect(partial(self.showWarning, "msg_%s" % device))
            self.alarm_layout.addWidget(button, 0, i + 2, 1, 1)
            setattr(self, "alarm_%s" % device, button)

        self.global_layout.addLayout(self.alarm_layout, 0, 0, 1, 3)

        self.watcher_alarm = QTimer(self)
        self.watcher_alarm.setInterval(1000)
        self.watcher_alarm.timeout.connect(self.checkCriticalValue)
        self.watcher_alarm.start()

    def getGroupBox(self):

        for i, boxes in enumerate(self.tab):
            tableName = boxes[0]
            deviceName = boxes[1]
            keywords = boxes[2].split(',')
            labels = boxes[3].split(',')
            groupBox = myGroupBox(self, tableName, deviceName, keywords, labels)
            self.global_layout.addWidget(groupBox, (i + 3) // 3, (i + 3) % 3)

        self.widget.setLayout(self.global_layout)
        self.global_layout.setRowStretch(0, 1)
        for l in range(1, self.global_layout.rowCount()):
            self.global_layout.setRowStretch(l, 3)
        self.setCentralWidget(self.widget)

    def checkCriticalValue(self):
        self.checkPressure()
        self.checkTurbo()
        self.checkGatevalve()
        self.checkCooler()

    def checkPressure(self):
        pressure_date, [pressure_val] = self.database.getLastData("xcu_r1__" + "pressure", "val1")
        if float(pressure_val) > 1e-4:
            self.msg_pressure = " Warning ! PRESSURE : %0.3e Torr is below 1e-4 Torr" % pressure_val
            self.setColor("QPushButton", self.alarm_pressure, "red")
        else:
            self.msg_pressure = "Pressure OK"
            self.setColor("QPushButton", self.alarm_pressure, "green")

    def checkTurbo(self):
        turbospeed_date, [turbospeed_val] = self.database.getLastData("xcu_r1__" + "turbospeed", "val1")
        if turbospeed_val < 90000:
            self.msg_turbo = " Warning ! TURBO SPEED is LOW : %i on 90000 RPM" % int(turbospeed_val)
            self.setColor("QPushButton", self.alarm_turbo, "red")
        else:
            self.msg_turbo = "Turbo OK"
            self.setColor("QPushButton", self.alarm_turbo, "green")

    def checkGatevalve(self):
        gatevalve_date, [gatevalve_val] = self.database.getLastData("xcu_r1__" + "gatevalve", "val1")
        if gatevalve_val != 253:
            self.msg_gatevalve = " Warning ! GATEVALVE is CLOSED"
            self.setColor("QPushButton", self.alarm_gatevalve, "red")
        else:
            self.msg_gatevalve = "Gatevalve OK"
            self.setColor("QPushButton", self.alarm_gatevalve, "green")

    def checkCooler(self):
        coolerPower_date, [coolerPower_val] = self.database.getLastData("xcu_r1__" + "coolertemps", "power")
        if coolerPower_val < 70 or coolerPower_val > 245:
            self.msg_cooler = " Warning ! COOLER POWER : % i W  Out of range 70-245 W" % int(coolerPower_val)
            self.setColor("QPushButton", self.alarm_cooler, "red")
        else:
            self.msg_cooler = "Cooler OK"
            self.setColor("QPushButton", self.alarm_cooler, "green")

    def setColor(self, type, widget, color):
        if type == "QLabel":
            widget.setStyleSheet(
                "%s { background-color : %s; color : white; qproperty-alignment: AlignCenter; font: 15pt;}" % (
                    type, color))
        else:
            widget.setStyleSheet("%s { background-color : %s; color : white; font: 15pt;}" % (type, color))

    def showWarning(self, attr):
        reply = QMessageBox.warning(self, 'Message', str(getattr(self, attr)), QMessageBox.Ok)

    def showError(self, nb_error):
        error_code = {-1: "The database is unreachable, check your network and your configuration",
                      -2: "They're not such columns / rows in your database", -3: "Bad format date",
                      -4: "No data to display"}
        reply = QMessageBox.critical(self, 'Message', error_code[nb_error], QMessageBox.Ok)

    def showInformation(self, information):
        reply = QMessageBox.information(self, 'Message', information, QMessageBox.Ok)

    def closeEvent(self, QCloseEvent):
        QCloseEvent.accept()
