#!/usr/bin/env python
# encoding: utf-8

from future import standard_library
standard_library.install_aliases()
from builtins import zip
from builtins import next
from builtins import str
import configparser
import pickle
from functools import partial

from ics_sps_engineering_Lib_dataQuery.databasemanager import DatabaseManager

try:
    from tabulate import tabulate

    Wiki = True
except ImportError:
    Wiki = False
import os
import numpy as np
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QMessageBox, QAction, QGridLayout, QTabWidget, QLabel, \
    QLineEdit, QCheckBox, QDialogButtonBox, QProgressDialog, QDialog
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

        self.tabCsv = {}
        self.moduleDict = {}

        self.configPath = path.split('ics_sps_engineering_monitorData')[0] + 'ics_sps_engineering_Lib_dataQuery'
        self.imgPath = path + "img/"

        self.initialize()
        self.getToolbar()
        self.getModes()

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

    def getModes(self):
        self.timerMode = QTimer(self)
        self.timerMode.setInterval(3000)
        self.timerMode.timeout.connect(self.handleModes)
        self.timerMode.start()

    def handleModes(self):
        sortedAlarm = self.readSortCfg(self.readAlarmCfg, '%s/alarm/' % self.configPath)
        for moduleName, alarms in list(sortedAlarm.items()):
            module = self.moduleDict[moduleName]
            mode = alarms[0]['mode']
            if mode != module.mode:
                module.setAlarms(alarms)

    def readSortCfg(self, func, path):
        sortedDict = {}
        cfg = func(path)
        for d in cfg:
            found = False
            for cuArm, cuLabel in list(mainWindow.cuArms.items()):
                if cuArm in d["tablename"]:
                    found = True
                    break
            if not found:
                cuLabel = "AIT"

            if cuLabel not in iter(list(sortedDict.keys())):

                sortedDict[cuLabel] = [d]
            else:
                sortedDict[cuLabel].append(d)

        return sortedDict

    def readDeviceCfg(self, path):
        datatype = configparser.ConfigParser()
        datatype.read('%s/datatype.cfg' % path)
        datatype = datatype._sections

        res = []
        allConfig = []
        all_file = next(os.walk(path))[-1]
        for f in all_file:
            config = configparser.ConfigParser()
            config.readfp(open(path + f))
            try:
                date = config.get('config_date', 'date')
                res.append((f, dt.datetime.strptime(date, "%d/%m/%Y")))
            except configparser.NoSectionError:
                pass

        res.sort(key=lambda tup: tup[1])
        config = configparser.ConfigParser()
        config.readfp(open(path + res[-1][0]))
        for a in config.sections():
            if a != 'config_date':
                allConfig.append({"tablename": a})
                for b in config.options(a):
                    allConfig[-1][b] = config.get(a, b)

                allConfig[-1]["unit"] = ','.join(
                    [datatype[typ.strip()]['unit'] for typ in config.get(a, "type").split(',')])

                if "label_device" not in config.options(a):
                    allConfig[-1]["label_device"] = (a.split('__')[1]).capitalize()
                if "label" not in config.options(a):
                    allConfig[-1]["label"] = config.get(a, "key")

        return allConfig

    def readAlarmCfg(self, path):
        listAlarm = []
        with open(path + 'mode.cfg', 'rb') as thisFile:
            unpickler = pickle.Unpickler(thisFile)
            modes = unpickler.load()

        for actor, mode in list(modes.items()):
            config = configparser.ConfigParser()
            config.readfp(open(path + '%s.cfg' % mode))
            sections = [a for a in config.sections() if actor in config.get(a, 'tablename')]
            for a in sections:
                dict = {"label": a, "mode": mode}
                for b in config.options(a):
                    dict[b] = config.get(a, b)
                listAlarm.append(dict)

        return listAlarm

    def getModule(self):

        sortedModule = self.readSortCfg(self.readDeviceCfg, '%s/config/' % self.configPath)
        sortedAlarm = self.readSortCfg(self.readAlarmCfg, '%s/alarm/' % self.configPath)

        for (moduleName, devices), (__, alarms) in zip(iter(list(sortedModule.items())), iter(list(sortedAlarm.items()))):
            module = Module(self, moduleName, devices)
            module.setAlarms(alarms)

            self.globalLayout.addWidget(module)
            self.moduleDict[moduleName] = module
            self.tabCsv[moduleName] = []

    def getIcons(self):

        arrowLeft = QPixmap()
        arrowRight = QPixmap()
        arrowLeft.load(self.imgPath + 'arrow_left.png')
        arrowRight.load(self.imgPath + 'arrow_right.png')
        self.iconArrLeft = QIcon(arrowLeft)
        self.iconArrRight = QIcon(arrowRight)

    def getToolbar(self):
        extract2csvAction = QAction(QIcon(self.os_path + 'img/spreadsheet.png'), 'Extract to Csv', self)
        extract2csvAction.triggered.connect(self.dialogExtract2csv)
        self.toolbar = self.addToolBar('Extract to Csv')
        self.toolbar.addAction(extract2csvAction)

    def dialogExtract2csv(self):
        d = QDialog(self)
        d.setFixedWidth(450)
        d.setWindowTitle("Extract data to Csv")
        d.setVisible(True)
        vbox = QVBoxLayout()
        tabWidget = QTabWidget()
        for name, mod in list(self.moduleDict.items()):
            wid = QWidget()
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
            for i, boxes in enumerate(mod.devices):
                checkbox = QCheckBox(boxes["label_device"])
                checkbox.stateChanged.connect(
                    partial(self.csvUpdateTab, name, checkbox,
                            [boxes["tablename"], boxes["key"], boxes["label"], boxes["unit"]]))
                checkbox.setCheckState(2)
                grid.addWidget(checkbox, 1 + i, 0, 1, 3)

            wid.setLayout(grid)
            tabWidget.addTab(wid, name)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.button(QDialogButtonBox.Ok).clicked.connect(
            partial(self.extract2csv, tabWidget, d, line_edit_begin, line_edit_end))
        buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(d.close)

        vbox.addWidget(tabWidget)
        vbox.addWidget(buttonBox)
        d.setLayout(vbox)

    def extract2csv(self, tabWidget, d, begin, end):
        name = tabWidget.tabText(tabWidget.currentIndex())
        end_id = np.inf if str(end.text()) == "Now" else str(end.text())
        fail = []
        progress = QProgressDialog("Extracting data", "Abort Extracting", 0, len(self.tabCsv) - 1)
        progress.setFixedSize(300, 200)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Extracting data...")
        for i, device in enumerate(self.tabCsv[name]):
            progress.setValue(i)
            ret = self.db.extract2csv(device[0], device[1], device[2], device[3], str(begin.text()), end_id)
            if ret is None: fail.append(device[0])
        if fail:
            self.showInformation("Extraction error on %s" % ','.join(fail))
        else:
            self.showInformation("Extraction Completed")
        d.close()

    def csvUpdateTab(self, module, checkbox, device):

        if checkbox.isChecked() and device not in self.tabCsv[module]:
            self.tabCsv[module].append(device)
        elif not checkbox.isChecked() and device in self.tabCsv[module]:
            self.tabCsv[module].remove(device)

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
