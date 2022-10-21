import os
import json
import tempfile

import pyblish.api
from openpype.hosts.tvpaint.api import lib


class ExportJsonAndPsd(pyblish.api.InstancePlugin):
    # Offset to get after ExtractConvertToEXR plugin.
    order = pyblish.api.ExtractorOrder + 0.2
    label = "Export JSON and PSD"
    hosts = ["tvpaint"]
    families = ["render"]

    enabled = False

    def process(self, instance):
        george_script_lines = []
        repres = instance.data.get("representations")
        if not repres:
            return

        new_repres = []
        for repre in repres:
            if repre['name'] != 'png':
                continue

            self.log.info("Processing representation: {}".format(
                json.dumps(repre, sort_keys=True, indent=4)
            ))

            output_dir = instance.data.get("stagingDir")
            if not output_dir or not os.path.exists(output_dir):
                # Create temp folder if staging dir is not set
                output_dir = (
                    tempfile.mkdtemp(prefix="tvpaint_export_json_psd_")
                ).replace("\\", "/")

            mark_in = repre['frameStart']
            mark_out = repre['frameEnd']
            new_filenames = []

            for filename in repre['files']:
                new_filename = os.path.splitext(filename)[0]
                dst_filepath = os.path.join(repre["stagingDir"], new_filename)
                new_filenames.append(new_filename + '.psd')

                george_script_lines.append(
                    "tv_clipsavestructure \"{}\" \"PSD\" \"image\" {}".format(dst_filepath, int(new_filename) - 1)
                )

            # george_script_lines.append(
            #     "tv_clipsavestructure \"{}\" \"JSON\" \"onlyvisiblelayers\" \"true\" \"patternfolder\" \"{}\" \"patternfile\" \"{}\"".format(
            #         "C:/Users/dev/Desktop/psds/json_export", "%ln_%4li", "%pfn_%ln_%3ii"
            #     )
            # )

            new_repres.append(
                {
                    "name": "psd",
                    "ext": "psd",
                    "files": new_filenames,
                    "stagingDir": repre["stagingDir"],
                    "tags": list(repre["tags"])
                }
            )
            
        lib.execute_george_through_file("\n".join(george_script_lines))

        instance.data["representations"].extend(new_repres)
        self.log.info(
            "Representations: {}".format(
                json.dumps(
                    instance.data["representations"], sort_keys=True, indent=4
                )
            )
        )
