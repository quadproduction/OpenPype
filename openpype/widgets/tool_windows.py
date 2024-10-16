from openpype.settings import get_project_settings
from openpype.pipeline import get_current_project_name
from qtpy import QtWidgets, QtCore


class BaseToolMixin:
    def __init__(self, *args, **kwargs):
        (parent,) = args

        self.project_name = get_current_project_name()

        # set a default value before trying to retrieve the value in the settings
        self.window_stays_on_top = False

        if self.project_name:
            settings = get_project_settings(self.project_name)
            self.window_stays_on_top = settings["global"].get("windows_stays_on_top", True)

        if self.window_stays_on_top:
            # To be able to activate the Stays On top feature, the window need have no parent.
            parent = None

        args = (parent,)

        super().__init__(*args, **kwargs)


class BaseToolDialog(BaseToolMixin, QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

    def showEvent(self, event):
        self.setWindowState(QtCore.Qt.WindowNoState)
        super().showEvent(event)
        self.setWindowState(QtCore.Qt.WindowActive)


class BaseToolWidget(BaseToolMixin, QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def showEvent(self, event):
        self.setWindowState(QtCore.Qt.WindowNoState)
        super().showEvent(event)
        self.setWindowState(QtCore.Qt.WindowActive)
