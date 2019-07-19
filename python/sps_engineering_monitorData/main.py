#!/usr/bin/env python
# encoding: utf-8

import argparse
import sys

from PyQt5.QtWidgets import QApplication
from window import MainWindow


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='tron', type=str, nargs='?',
                        help='PostgreSQL host')
    parser.add_argument('--port', default=5432, type=int, nargs='?',
                        help='PostgreSQL port')
    parser.add_argument('--password', default='', type=str, nargs='?',
                        help='PostgreSQL password')
    parser.add_argument('--dbname', default='archiver', type=str, nargs='?',
                        help='Database name')
    args = parser.parse_args()
    app = QApplication(sys.argv)

    w = MainWindow(**vars(args))
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
