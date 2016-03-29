#!/usr/bin/env python
# encoding: utf-8
import os
import sys

from PyQt5.QtWidgets import QApplication

absolute_path = os.getcwd() + '/' + sys.argv[0].split('main.py')[0]
sys.path.insert(0, absolute_path.split('ics_sps_engineering_monitorData')[0])

from window import mainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    addr = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = sys.argv[2] if len(sys.argv) > 2 else 5432
    actor = sys.argv[3] if len(sys.argv) > 3 else "xcu_r1"
    w = mainWindow(absolute_path, addr, port, actor)
    sys.exit(app.exec_())
