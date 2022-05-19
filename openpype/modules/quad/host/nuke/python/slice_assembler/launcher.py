# -*- coding: utf-8 -*-

import nuke

from PySide2 import QtCore, QtGui, QtWidgets
from shiboken2 import wrapInstance

from . import view


def run():
    """Launchs the view
    Returns:
        None
    """
    global SLICEVIEW
    # global iPanel #

    app = QtWidgets.QApplication.instance()

    def get_main_window():
        """""get nukes main window""
        Returns:
            widget -- nuke's main window
        """
        for widget in app.topLevelWidgets():
            if widget.metaObject().className() == 'Foundry::UI::DockMainWindow':
                return widget

    main_window = get_main_window()

    # Close the window if already opened
    if 'SLICEVIEW' in globals():
        SLICEVIEW.close()

    # Create an instance of ViewInterface from view.py
    SLICEVIEW = view.SLCView(main_window)
    # Display
    SLICEVIEW.show()
