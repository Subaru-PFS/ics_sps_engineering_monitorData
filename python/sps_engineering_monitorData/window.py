#!/usr/bin/env python
# encoding: utf-8


import pickle
from functools import partial

import configparser
import sps_engineering_Lib_dataQuery as dataQuery
import sps_engineering_monitorData.img as imgFolder
from sps_engineering_Lib_dataQuery.databasemanager import DatabaseManager

try:
    from tabulate import tabulate

    Wiki = True
except ImportError:
    Wiki = False
import os
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QMessageBox, QAction, QGridLayout, QTabWidget, QLabel, \
    QLineEdit, QCheckBox, QDialogButtonBox, QDialog, QProgressBar
import datetime as dt
from module import Module
from PyQt5.QtGui import QPixmap, QIcon


class mainWindow(QMainWindow):
    cuArms = {"_r1__": "One-channel RCU",
              "_b1__": "One-channel BCU",
              "_r0__": "Thermal RCU",
              }

    def __init__(self, display, ip, port):
        super(mainWindow, self).__init__()

        self.display = display
        self.db = DatabaseManager(ip, port)
        self.networkError = False
        self.configPath = os.path.dirname(dataQuery.__file__)
        self.tabCsv = {}
        self.moduleDict = {}

        self.imgPath = os.path.dirname(imgFolder.__file__)

        self.initialize()
        self.getToolbar()
        self.getModes()

    def initialize(self):

        self.mainWidget = QWidget()
        self.globalLayout = QVBoxLayout()
        self.db.init()

        self.getIcons()
        self.getModule()

        self.menubar = self.menuBar()
        self.about_action = QAction('About', self)
        self.about_action.triggered.connect(partial(self.showInformation, "monitorData 1.0.5 \n\r made for PFS by ALF"))
        self.helpMenu = self.menubar.addMenu('&?')
        self.helpMenu.addAction(self.about_action)

        self.center = [300, 300]
        self.title = "ics_sps_engineering_monitorData"
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
        all_file = [f for f in next(os.walk(path))[-1] if '.cfg' in f]
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

        for moduleName in sorted(sortedModule.keys()):
            devices = sortedModule[moduleName]
            alarms = sortedAlarm[moduleName]
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
        extract2csvAction = QAction(QIcon('%s/%s' % (self.imgPath, 'spreadsheet.png')), 'Extract to Csv', self)
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
            wid.dateStart = QLineEdit('%s00:00' % dt.datetime.now().strftime("%Y-%m-%dT"))
            wid.dateEnd = QLineEdit("Now")
            grid.addWidget(QLabel("From"), 0, 0)
            grid.addWidget(wid.dateStart, 0, 1)
            grid.addWidget(QLabel("To"), 0, 2)
            grid.addWidget(wid.dateEnd, 0, 3)
            for i, boxes in enumerate(mod.devices):
                checkbox = QCheckBox(boxes["label_device"])
                checkbox.stateChanged.connect(partial(self.csvUpdateTab, name, checkbox, boxes))
                checkbox.setCheckState(2)
                grid.addWidget(checkbox, 1 + i, 0, 1, 3)

            wid.setLayout(grid)
            tabWidget.addTab(wid, name)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.button(QDialogButtonBox.Ok).clicked.connect(partial(self.extract2csv, tabWidget, d))
        buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(d.close)

        vbox.addWidget(tabWidget)
        vbox.addWidget(buttonBox)
        d.setLayout(vbox)

    def extract2csv(self, tabWidget, d):
        name = tabWidget.tabText(tabWidget.currentIndex())
        wid = tabWidget.currentWidget()
        start = wid.dateStart.text()
        end = wid.dateEnd.text()
        end = False if end == 'Now' else end

        fail = []
        progress = QProgressBar()

        progress.setRange(0, len(self.tabCsv))
        d.layout().addWidget(progress)
        progress.setValue(0)

        for i, device in enumerate(self.tabCsv[name]):
            try:
                dataFrame = self.db.dataBetween(device['tablename'], device['key'], start=start, end=end)
                dataFrame.to_csv('/tmp/PFS-%s-%s.csv' % (start[:-6], device['tablename']))
                progress.setValue(i + 1)
            except:
                fail.append(device['tablename'])

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
