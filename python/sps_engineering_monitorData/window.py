#!/usr/bin/env python
# encoding: utf-8

try:
    from tabulate import tabulate

    Wiki = True
except ImportError:
    Wiki = False

from functools import partial

import sps_engineering_Lib_dataQuery as dataQuery
import sps_engineering_monitorData as monitorData
import os
import datetime as dt

from sps_engineering_Lib_dataQuery.databasemanager import DatabaseManager
from sps_engineering_Lib_dataQuery.confighandler import loadAlarm, loadConf

from PyQt5.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QMessageBox, QAction, QGridLayout, QTabWidget, QLabel, \
    QLineEdit, QCheckBox, QDialogButtonBox, QDialog, QProgressBar
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap, QIcon, QResizeEvent
from module import Module


class MainWindow(QMainWindow):
    cuArms = {'_r1__': 'SM1 RCU',
              '_b1__': 'SM1 BCU',
              }

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__()

        self.db = DatabaseManager(**kwargs)
        self.networkError = False
        self.alarmPath = os.path.abspath(os.path.join(os.path.dirname(dataQuery.__file__), '../..', 'alarm'))
        self.tabCsv = {}
        self.moduleDict = {}

        self.imgPath = os.path.abspath(os.path.join(os.path.dirname(monitorData.__file__), '../..', 'img'))
        self.initialize()

    def initialize(self):

        self.mainWidget = QWidget()
        self.globalLayout = QVBoxLayout()
        self.db.init()

        self.getIcons()
        self.getModule()
        self.getMenu()
        self.getToolbar()
        self.getTimer()

        self.center = [300, 300]
        self.title = "ics_sps_engineering_monitorData"
        self.move(self.center[0], self.center[1])
        self.setWindowTitle(self.title)

        self.mainWidget.setLayout(self.globalLayout)
        self.setCentralWidget(self.mainWidget)
        self.show()

    def getMenu(self):

        self.menubar = self.menuBar()
        self.about_action = QAction('About', self)
        self.about_action.triggered.connect(partial(self.showInformation, "monitorData 1.0.5 \n\r made for PFS by ALF"))
        self.helpMenu = self.menubar.addMenu('&?')
        self.helpMenu.addAction(self.about_action)

    def getTimer(self):
        self.timerData = QTimer(self)
        self.timerData.setInterval(10000)
        self.timerData.timeout.connect(self.updateGUI)
        self.timerData.start()

    def updateGUI(self):
        self.handleModes()
        for module in self.moduleDict.values():
            module.waitforData()

    def handleModes(self):
        allAlarms = loadAlarm()
        sortedAlarms = self.sortCfg(allAlarms)

        for moduleName, alarms in list(sortedAlarms.items()):
            module = self.moduleDict[moduleName]
            mode = alarms[0].mode if alarms else 'offline'
            if mode != module.mode:
                module.setAlarms(alarms)

    def sortCfg(self, config):
        sortedDict = {label: [] for label in list(MainWindow.cuArms.values()) + ['AIT']}

        for dev in config:
            found = False
            for cuArm in list(MainWindow.cuArms.keys()):
                if cuArm in dev.tablename:
                    found = True
                    break
            cuLabel = MainWindow.cuArms[cuArm] if found else 'AIT'

            sortedDict[cuLabel].append(dev)

        return sortedDict

    def getModule(self):

        allModules = loadConf()
        allAlarms = loadAlarm()

        sortedModule = self.sortCfg(allModules)
        sortedAlarms = self.sortCfg(allAlarms)

        for moduleName in sorted(sortedModule.keys()):
            devices = sortedModule[moduleName]
            alarms = sortedAlarms[moduleName]
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
            for i, device in enumerate(mod.devices):
                checkbox = QCheckBox(device.deviceLabel)
                checkbox.stateChanged.connect(partial(self.csvUpdateTab, name, checkbox, device))
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
                dataFrame = self.db.dataBetween(device.tablename, ','.join(device.keys), start=start, end=end)
                dataFrame.to_csv('/tmp/PFS-%s-%s.csv' % (start[:-6], device.tablename))
                progress.setValue(i + 1)
            except Exception as e:
                print(e)
                fail.append(device.tablename)

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
