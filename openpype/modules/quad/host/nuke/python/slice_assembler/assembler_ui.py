# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/lamagagoo/Library/Preferences/Autodesk/maya/2018/scripts/slice_assembler/assembler_ui.ui'
#
# Created: Sun Mar 22 15:12:43 2020
#      by: pyside2-uic  running on PySide2 2.0.0~alpha0
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(678, 269)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.gbox_origine = QtWidgets.QGroupBox(self.centralwidget)
        self.gbox_origine.setObjectName("gbox_origine")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.gbox_origine)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.le_origine = QtWidgets.QLineEdit(self.gbox_origine)
        self.le_origine.setObjectName("le_origine")
        self.horizontalLayout.addWidget(self.le_origine)
        self.pb_origine = QtWidgets.QPushButton(self.gbox_origine)
        self.pb_origine.setObjectName("pb_origine")
        self.horizontalLayout.addWidget(self.pb_origine)
        self.gridLayout.addWidget(self.gbox_origine, 0, 0, 1, 1)
        self.gbox_destination = QtWidgets.QGroupBox(self.centralwidget)
        self.gbox_destination.setObjectName("gbox_destination")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.gbox_destination)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.le_destination = QtWidgets.QLineEdit(self.gbox_destination)
        self.le_destination.setObjectName("le_destination")
        self.horizontalLayout_2.addWidget(self.le_destination)
        self.pb_destination = QtWidgets.QPushButton(self.gbox_destination)
        self.pb_destination.setObjectName("pb_destination")
        self.horizontalLayout_2.addWidget(self.pb_destination)
        self.gridLayout.addWidget(self.gbox_destination, 1, 0, 1, 1)
        self.pb_assemble = QtWidgets.QPushButton(self.centralwidget)
        self.pb_assemble.setObjectName("pb_assemble")
        self.gridLayout.addWidget(self.pb_assemble, 2, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar()
        self.menubar.setGeometry(QtCore.QRect(0, 0, 678, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "Slice Assemebler", None, -1))
        self.gbox_origine.setTitle(QtWidgets.QApplication.translate("MainWindow", "Source", None, -1))
        self.le_origine.setPlaceholderText(QtWidgets.QApplication.translate("MainWindow", "Source Path", None, -1))
        self.pb_origine.setText(QtWidgets.QApplication.translate("MainWindow", "Browse", None, -1))
        self.gbox_destination.setTitle(QtWidgets.QApplication.translate("MainWindow", "Destination", None, -1))
        self.le_destination.setPlaceholderText(QtWidgets.QApplication.translate("MainWindow", "Destination Path", None, -1))
        self.pb_destination.setText(QtWidgets.QApplication.translate("MainWindow", "Browse", None, -1))
        self.pb_assemble.setText(QtWidgets.QApplication.translate("MainWindow", "Assemble", None, -1))

