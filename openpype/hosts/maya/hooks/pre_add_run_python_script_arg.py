import os
import sys
from pathlib import Path

from openpype.lib.applications import PreLaunchHook, LaunchTypes


class AddMayaPythonScriptToLaunchArgs(PreLaunchHook):
    """ Modify launch arguments to execute Python script in Maya non-GUI mode """

    # Append after file argument
    order = 15
    app_groups = {"maya"}
    launch_types = {LaunchTypes.local}

    def execute(self):
        
        if "script_launch_data" not in self.launch_context.data:
            return
        script_launch_data = self.launch_context.data["script_launch_data"]

        if "script_path" not in script_launch_data:
            self.log.warning(
                f"Python script not specified"
            )
            return

        script_path = Path(script_launch_data["script_path"])
        if not script_path.exists():
            self.log.warning(
                f"Python script {script_path} doesn't exist. "
                "Skipped..."
            )
            return

        if "file_path" not in script_launch_data:
            self.log.warning(
                f"File path not specified"
            )
            return
        
        file_path = Path(script_launch_data["file_path"])
        if not file_path.exists():
            self.log.warning(
                f"File path {script_path} doesn't exist. Skipped..."
            )
            return

        maya_exe = self.launch_context.launch_args[0]
        mayapy_exe = os.path.join(os.path.dirname(maya_exe), "mayapy")
        if sys.platform == "windows":
            mayapy_exe += ".exe"
            mayapy_exe = os.path.normpath(mayapy_exe)

        self.launch_context.launch_args = [
            mayapy_exe,
            str(script_path),
            str(file_path),
        ]
