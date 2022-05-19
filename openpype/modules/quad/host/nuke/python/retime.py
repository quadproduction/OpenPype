# -*- coding: utf-8 -*-

import json
import os
import nuke
from PySide2 import QtWidgets

__author__ = "HASHEMIZADEH Mohammad"


def j_retime(json_file=None):
    """Retime the scene base on the given Json data.

    Args:
        json_file (str): Json file.
    """
    with open(json_file, 'r') as json_read:
        data = json.load(json_read)
        if "timewarp_values" not in data:
            print("No readable data in Json!")
            return

        timewarp_values = {
            float(k): float(v) for k, v in data["timewarp_values"].items()
        }
        # Create an oflow node
        # oflow = nuke.createNode('OFlow2', 'timing2 Frame', inpanel=False)
        # oflow['timingFrame2'].setAnimated()
        # Create a TimeWarp node [2eme solution]
        time_warp = nuke.createNode('TimeWarp', inpanel=False)
        time_warp['lookup'].setAnimated()
        for frame in sorted(timewarp_values.keys()):
            # print frame, timewarp_values[frame]
            # oflow['timingFrame2'].setValueAt(timewarp_values[frame], frame)
            time_warp['lookup'].setValueAt(timewarp_values[frame], frame)
        print("Done!")


def run():
    """Runs the UI and pass the json file path to the retime func
    """
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
    # get start path from Read node, otherwise /prod/
    home_path = "/prod/"
    selected_nodes = nuke.selectedNodes()
    if selected_nodes and selected_nodes[0].Class() == 'Read':
        read_file = selected_nodes[0].knob('file').value()
        home_path, _ = os.path.split(read_file)

    json_file = QtWidgets.QFileDialog.getOpenFileName(
        main_window,
        "Select Time Warp Json",
        home_path,
        "Json File (*.json)")[0]

    if not json_file:
        return
    if not os.path.exists(json_file):
        print("\t\t/!\\ Json does not exist: %s" % json_file)
        return
    j_retime(json_file)
