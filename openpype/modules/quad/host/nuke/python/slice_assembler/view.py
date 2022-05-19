# -*- coding: utf-8 -*-
__author__ = "HASHEMIZADEH Mohammad"

from PySide2 import QtCore, QtGui, QtWidgets
import sys
import os


from . import assembler_ui
from . import slice_assembler


class SLCView(QtWidgets.QMainWindow, assembler_ui.Ui_MainWindow):
    def __init__(self, parent = None):
        """
        Initialize the UVMaskView.
        """
        QtWidgets.QMainWindow.__init__(self,parent)
        self.setupUi(self)

        # CONNECTIONS
        self.pb_origine.clicked.connect(self.get_source_path)
        self.pb_destination.clicked.connect(self.get_destination_path)
        self.pb_assemble.clicked.connect(self.assemble)

    def get_source_path(self):
        dir_name = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Source Path",
            os.path.expanduser('~'),
            QtWidgets.QFileDialog.ShowDirsOnly|QtWidgets.QFileDialog.DontResolveSymlinks
        )
        if dir_name:
            self.le_origine.setText(dir_name)

    def get_destination_path(self):
        dir_name = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Destination Path",
            os.path.expanduser('~'),
            QtWidgets.QFileDialog.ShowDirsOnly|QtWidgets.QFileDialog.DontResolveSymlinks
        )
        if dir_name:
            self.le_destination.setText(dir_name)


    def assemble(self):
        if os.path.isdir(self.le_origine.text()) and os.path.isdir(self.le_destination.text()):
            origin = self.le_origine.text()
            destination = self.le_destination.text()
            slice_assembler.run(origin, destination)
        else:
            print("Error: Verify directory information")

    def unicode_to_str(self, texte=None):
        """Encode given unicode to str

        Keyword Arguments:
            texte {unicode} -- given unicode string (default: {None})

        Returns:
            str -- encoded string
        """
        if isinstance(texte, unicode):
            texte = texte.encode('utf-8')
        return texte
