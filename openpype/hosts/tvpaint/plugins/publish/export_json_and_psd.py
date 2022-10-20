import os
import json
import tempfile

import pyblish.api
from openpype.hosts.tvpaint.api import lib


class ExportJsonAndPsd(pyblish.api.InstancePlugin):
    # Offset to get after ExtractConvertToEXR plugin.
    order = pyblish.api.ExtractorOrder + 0.2
    label = "Export Json and PSD"
    hosts = ["tvpaint"]
    families = ["render"]

    enabled = False

    def process(self, instance):
        george_script_lines = []
        repres = instance.data.get("representations")
        if not repres:
            return

        for repre in repres:
            if repre['name'] != 'png':
                continue

            self.log.info("Processing representation: {}".format(
                json.dumps(repre, sort_keys=True, indent=4)
            ))

            output_dir = instance.data.get("stagingDir")
            if not output_dir:
                # Create temp folder if staging dir is not set
                output_dir = (
                    tempfile.mkdtemp(prefix="tvpaint_export_json_psd_")
                ).replace("\\", "/")

            mark_in = repre['frameStart']
            mark_out = repre['frameEnd']

            for frame in range(mark_in, mark_out + 1):
                output_dir = "/".join(["C:/Users/dev/Desktop/psds", str(frame - 1)])
                george_script_lines.append(
                    "tv_clipsavestructure \"{}\" \"PSD\" \"image\" {}".format(output_dir, frame - 1)
                )
            george_script_lines.append(
                "tv_clipsavestructure \"{}\" \"JSON\" \"onlyvisiblelayers\" \"true\" \"patternfolder\" \"{}\" \"patternfile\" \"{}\"".format(
                    "C:/Users/dev/Desktop/psds/json_export", "%ln_%4li", "%pfn_%ln_%3ii"
                )
            )
            
            lib.execute_george_through_file("\n".join(george_script_lines))
