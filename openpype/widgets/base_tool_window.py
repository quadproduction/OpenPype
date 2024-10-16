from openpype.settings import get_project_settings
from openpype.pipeline import legacy_io
from qtpy import QtWidgets
import platform


class BaseToolWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        self.project_name = legacy_io.active_project()

        # set a default value before trying to retrieve the value in the settings
        self.window_stays_on_top = False

        if self.project_name:
            settings = get_project_settings(self.project_name)
            self.window_stays_on_top = settings["global"].get("windows_stays_on_top", True)

        if self.window_stays_on_top:
            # To be able to activate the Stays On top feature, the window need have no parent.
            parent = None

        super().__init__(parent)

    def showEvent(self, event):
        super(BaseToolWindow, self).showEvent(event)
        if platform.system().lower() == "windows:":
            from win32gui import SetWindowPos
            import win32con

            SetWindowPos(
                self.winId(),
                win32con.HWND_TOPMOST,  # = always on top. only reliable way to bring it to the front on windows
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
            )
            SetWindowPos(
                self.winId(),
                win32con.HWND_NOTOPMOST,  # disable the always on top, but leave window at its top position
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
            )
