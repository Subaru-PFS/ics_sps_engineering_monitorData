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
from PyQt5.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QMessageBox, QAction
import datetime as dt
from module import Module
from PyQt5.QtGui import QPixmap, QIcon


class mainWindow(QMainWindow):
    cuArms = {"_r1__": "One-channel RCU",
              "_b1__": "One-channel BCU",
              "_r0__": "Thermal RCU",
              }

    def __init__(self, display, path, ip, port):
        super(mainWindow, self).__init__()

        self.display = display
        self.db = DatabaseManager(ip, port)
        self.networkError = False
        self.os_path = path

        self.tabCsv = []

        self.moduleDict = {}
        self.sortedModule = {}

        self.configPath = path.split('ics_sps_engineering_monitorData')[0] + 'ics_sps_engineering_Lib_dataQuery/config/'
        self.imgPath = path + "img/"

        self.readCfg(self.configPath)

        self.initialize()
        #self.getToolbar()

    def initialize(self):

        self.mainWidget = QWidget()
        self.globalLayout = QVBoxLayout()
        no_err = self.db.initDatabase()

        if no_err != -1:
            self.getIcons()
            self.getModule()

        else:
            self.showError(no_err)

        self.menubar = self.menuBar()
        self.about_action = QAction('About', self)
        self.about_action.triggered.connect(
            partial(self.showInformation, "MonitorActor 0.7 working with lib_DataQuery 0.7\n\r made for PFS by ALF"))
        self.helpMenu = self.menubar.addMenu('&?')
        self.helpMenu.addAction(self.about_action)

        self.center = [300, 300]
        self.title = " AIT-PFS Monitoring CU"
        self.move(self.center[0], self.center[1])
        self.setWindowTitle(self.title)

        self.mainWidget.setLayout(self.globalLayout)
        self.setCentralWidget(self.mainWidget)
        self.show()

    def readCfg(self, path):
        deviceConfig = self.readDeviceCfg(path)
        alarmConfig = self.readAlarmCfg(path)

        for i, conf in enumerate([deviceConfig, alarmConfig]):
            for d in conf:
                found = False
                for cuArm, cuLabel in mainWindow.cuArms.iteritems():
                    if cuArm in d["tablename"]:
                        found = True
                        break
                if not found:
                    cuLabel = "AIT"

                if cuLabel not in self.sortedModule.iterkeys():

                    self.sortedModule[cuLabel] = ([d], []) if i == 0 else ([], [d])
                else:
                    self.sortedModule[cuLabel][i].append(d)

    def readDeviceCfg(self, path):

        res = []
        allConfig = []
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
                allConfig.append({"tablename": a})
                for b in config.options(a):
                    allConfig[-1][b] = config.get(a, b)

        return allConfig

    def readAlarmCfg(self, path):

        listAlarm = []
        config = ConfigParser.ConfigParser()
        config.readfp(open(path + 'alarm.cfg'))
        for a in config.sections():
            dict = {"label": a}
            for b in config.options(a):
                dict[b] = config.get(a, b)
            listAlarm.append(dict)

        return listAlarm

    def getModule(self):

        for moduleName, (devices, alarms) in self.sortedModule.iteritems():
            module = Module(self, moduleName, devices, alarms)
            self.globalLayout.addWidget(module)
            self.moduleDict[moduleName] = module

    def getIcons(self):

        arrowLeft = QPixmap()
        arrowRight = QPixmap()
        arrowLeft.load(self.imgPath + 'arrow_left.png')
        arrowRight.load(self.imgPath + 'arrow_right.png')
        self.iconArrLeft = QIcon(arrowLeft)
        self.iconArrRight = QIcon(arrowRight)

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
