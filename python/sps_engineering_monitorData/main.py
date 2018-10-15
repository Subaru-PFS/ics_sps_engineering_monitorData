#!/usr/bin/env python
# encoding: utf-8
import os
import sys

from PyQt5.QtWidgets import QApplication
from window import MainWindow
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='localhost', type=str, nargs='?',
                        help='PostgreSQL host')
    parser.add_argument('--port', default=5432, type=int, nargs='?',
                        help='PostgreSQL port')
    parser.add_argument('--password', default='', type=str, nargs='?',
                        help='PostgreSQL password')
    args = parser.parse_args()
    app = QApplication(sys.argv)

    display = app.desktop().screenGeometry().width(), app.desktop().screenGeometry().height()
    w = MainWindow(display, args.host, args.port, args.password)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

