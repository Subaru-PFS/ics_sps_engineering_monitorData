#!/usr/bin/env python
# encoding: utf-8

import ConfigParser
from functools import partial

from ics_sps_engineering_Lib_dataQuery.databasemanager import DatabaseManager

try:
    from tabulate import tabulate

    Wiki = True
except ImportError:
    Wiki = False
import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QGridLayout, QLabel, QMessageBox, QAction, QDialog, \
    QDialogButtonBox, QLineEdit, QCheckBox, \
    QApplication, QProgressDialog
from PyQt5.QtGui import QIcon
from alarm import alarmChecker
from myqgroupbox import myGroupBox
import numpy as np
import datetime as dt


class mainWindow(QMainWindow):
    def __init__(self, display, path, ip, port):
        super(mainWindow, self).__init__()
        self.divcoeff = 4 if display[1] < 900 else 3
        self.db = DatabaseManager(ip, port)
        self.networkError = False
        self.os_path = path
        self.tab = []
        self.tabCsv = []
        self.low_bound = {}
        self.high_bound = {}
        self.device_dict = {}
        self.config_path = path.split('ics_sps_engineering_monitorData')[
                               0] + 'ics_sps_engineering_Lib_dataQuery/config/'
        self.readCfg(self.config_path)
        self.initialize()
        self.getToolbar()
        print self.height()

    def initialize(self):

        self.widget = QWidget()
        self.global_layout = QGridLayout()
        no_err = self.db.initDatabase()
        if no_err != -1:
            self.getAlarm()
            self.getGroupBox()
        else:
            self.showError(no_err)

        self.menubar = self.menuBar()
        self.about_action = QAction('About', self)
        self.about_action.triggered.connect(
            partial(self.showInformation, "MonitorActor v0.6 working with lib_DataQuery v0.6\n\r made for PFS by ALF"))
        self.helpMenu = self.menubar.addMenu('&?')
        self.helpMenu.addAction(self.about_action)
        self.center = [300, 300]
        self.title = " AIT-PFS Monitoring CU"
        self.move(self.center[0], self.center[1])
        self.setWindowTitle(self.title)
        self.show()

    def getToolbar(self):
        extract2csvAction = QAction(QIcon(self.os_path + 'img/spreadsheet.png'), 'Extract to Csv', self)
        extract2csvAction.triggered.connect(self.dialogExtract2csv)
        wikiAction = QAction(QIcon(self.os_path + 'img/wiki.png'), 'Copy to MediaWiki', self)
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
            checkbox = QCheckBox(boxes["label_device"])
            checkbox.stateChanged.connect(
                partial(self.csvUpdateTab, checkbox, [boxes["tableName"], boxes["key"], boxes["label"], boxes["unit"]]))
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
        end_id = np.inf if str(end.text()) == "Now" else str(end.text())
        fail = []
        progress = QProgressDialog("Extracting data", "Abort Extracting", 0, len(self.tabCsv) - 1)
        progress.setFixedSize(300, 200)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Extracting data...")
        for i, device in enumerate(self.tabCsv):
            progress.setValue(i)
            ret = self.db.extract2csv(device[0], device[1], device[2], device[3], str(begin.text()), end_id)
            if ret is None: fail.append(device[0])
        if fail:
            self.showInformation("Extraction error on %s" % ','.join(fail))
        else:
            self.showInformation("Extraction Completed")
        d.close()

    def copy2wiki(self):
        if Wiki:
            config = ConfigParser.ConfigParser()
            config.readfp(open(self.os_path + "config/mediawiki.cfg"))
            selectdata = []
            for a in config.sections():
                selectdata.append([a])
                for b in config.options(a):
                    selectdata[-1].append(config.get(a, b))

            data_list = [["Sensor Name", "Temp. Value", "Unit", "Read by", "Type", "Cold/warm"]]
            for i, groups in enumerate(selectdata):
                tableName = groups[0]
                keys = groups[2]
                labels = groups[3].split(',')
                typeName = groups[4]
                deviceName = groups[1]
                unitName = groups[5].split(',') if len(groups[5].split(',')) > 1 else len(labels) * [groups[5]]
                typeTemps = groups[6].split(',')
                dates, vals = self.db.getLastData(tableName, keys)

                for (key, val, ttemp, unit) in zip(labels, vals, typeTemps, unitName):
                    data_list.append([key, val, unit, deviceName, typeName, ttemp])

            wikistr = tabulate(data_list, headers="firstrow", tablefmt="mediawiki")
            wikihead = "{| class=\"wikitable sortable centre\" style=\"text-align: left;\"" + "\n" + "|+ Temperature sensors value " + str(
                dates) + "\n"

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
        res = []
        all_file = next(os.walk(path))[-1]
        for f in all_file:
            config = ConfigParser.ConfigParser()
            config.readfp(open(path + f))
            try:
                date = config.get('config_date', 'date')
                res.append((f, dt.datetime.strptime(date, "%d/%m/%Y")))
            except ConfigParser.NoSectionError:
                pass
        res.sort(key=lambda tup: tup[1])
        config = ConfigParser.ConfigParser()
        config.readfp(open(path + res[-1][0]))
        for a in config.sections():
            if a != 'config_date':
                self.device_dict[a] = ""
                self.tab.append({"tableName": a})
                for b in config.options(a):
                    if b == "lower_bound":
                        keys = config.get(a, "key").split(',')
                        minimums = config.get(a, "lower_bound").split(',')
                        maximums = config.get(a, "higher_bound").split(',')
                        for low_bound, high_bound, key in zip(minimums, maximums, keys):
                            self.low_bound[a + key] = float(low_bound)
                            self.high_bound[a + key] = float(high_bound)
                    elif b == "higher_bound":
                        pass

                    else:
                        self.tab[-1][b] = config.get(a, b)

    def getAlarm(self):

        self.alarm_widget = alarmChecker(parent=self)
        self.global_layout.addWidget(self.alarm_widget, 0, 0, 1, self.divcoeff)

    def getGroupBox(self):

        for i, boxes in enumerate(self.tab):
            tableName = boxes["tableName"]
            deviceName = boxes["label_device"]
            keys = boxes["key"].split(',')
            labels = boxes["label"].split(',')
            units = boxes["unit"].split(',')
            groupBox = myGroupBox(self, tableName, deviceName, keys, labels, units)
            self.global_layout.addWidget(groupBox, (i + self.divcoeff) // self.divcoeff,
                                         (i + self.divcoeff) % self.divcoeff)

        self.widget.setLayout(self.global_layout)
        self.global_layout.setRowStretch(0, 1)
        for l in range(1, self.global_layout.rowCount()):
            self.global_layout.setRowStretch(l, self.divcoeff)
        self.setCentralWidget(self.widget)

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
