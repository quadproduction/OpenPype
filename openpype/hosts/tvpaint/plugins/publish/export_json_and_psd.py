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
        if not self.psd_export and not self.json_export:
            self.log.warning("PSD and JSON export are not enabled. Please check your project settings.")
            return

        george_script_lines = []
        repres = instance.data.get("representations")
        if not repres:
            return

        new_psd_repres = []
        new_json_repres = []
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

            new_filenames = []

            if self.psd_export:
                for filename in repre['files']:
                    new_filename = os.path.splitext(filename)[0]
                    dst_filepath = os.path.join(repre["stagingDir"], new_filename)
                    new_filenames.append(new_filename + '.psd')

                    george_script_lines.append(
                        "tv_clipsavestructure \"{}\" \"PSD\" \"image\" {}".format(dst_filepath, int(new_filename) - 1)
                    )
                
                new_psd_repres.append(
                    {
                        "name": "psd",
                        "ext": "psd",
                        "files": new_filenames,
                        "stagingDir": output_dir,
                        "tags": list(repre["tags"])
                    }
                )

            if self.json_export:
                george_script_lines.append(
                    "tv_clipsavestructure \"{}\" \"JSON\" \"onlyvisiblelayers\" \"true\" \"patternfolder\" \"{}\" \"patternfile\" \"{}\"".format(
                        os.path.join(output_dir, 'json_files'), "%ln_%4li", "%pfn_%ln_%3ii"
                    )
                )

                new_json_repres.append(
                    {
                        "name": "json",
                        "ext": "json",
                        "files": 'json_files.json',
                        "stagingDir": output_dir,
                        "tags": list(repre["tags"])
                    }
                )
            
        lib.execute_george_through_file("\n".join(george_script_lines))

        instance.data["representations"].extend(new_psd_repres)
        instance.data["representations"].extend(new_json_repres)
        self.log.info(
            "Representations: {}".format(
                json.dumps(
                    instance.data["representations"], sort_keys=True, indent=4
                )
            )
        )
