import os
import json

import pyblish.api
from openpype.hosts.tvpaint.api import lib


class ExportJsonAndPsd(pyblish.api.InstancePlugin):
    order = pyblish.api.ExtractorOrder + 0.1
    label = "Export Json and PSD"
    hosts = ["tvpaint"]
    families = ["render"]

    enabled = False

    def process(self, instance):
        repres = instance.data.get("representations")
        if not repres:
            return

        self.log.info("####################################")
        self.log.info(repres)
        # george_script_lines = [
        #     # Change bg color to color from settings
        #     "tv_background \"color\" {} {} {}".format(*bg_color),
        #     "tv_SaveMode \"PNG\"",
        #     "export_path = \"{}\"".format(
        #         first_frame_filepath.replace("\\", "/")
        #     ),
        #     "tv_savesequence '\"'export_path'\"' {} {}".format(
        #         mark_in, mark_out
        #     )
        # ]

        # lib.execute_george_through_file("\n".join(george_script_lines))
