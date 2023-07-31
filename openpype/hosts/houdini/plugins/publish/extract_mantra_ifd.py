import os

import pyblish.api

from openpype.pipeline import publish

import hou


class ExtractMantraIFD(publish.Extractor):

    order = pyblish.api.ExtractorOrder
    label = "Extract Mantra ifd"
    hosts = ["houdini"]
    families = ["mantraifd"]
    targets = ["local", "remote"]

    def process(self, instance):
        if instance.data.get("farm"):
            self.log.debug("Should be processed on farm, skipping.")
            return

        ropnode = hou.node(instance.data.get("instance_node"))
        output = ropnode.evalParm("soho_diskfile")
        staging_dir = os.path.dirname(output)
        instance.data["stagingDir"] = staging_dir
        file_name = os.path.basename(output)

        files = instance.data["frames"]
        missing = []
        for file_name in files:
            full_path = os.path.normpath(os.path.join(staging_dir, file_name))
            if not os.path.exists(full_path):
                missing.append(full_path)

        if missing:
            raise RuntimeError("Failed to complete Mantra ifd extraction. "
                               "Missing output files: {}".format(missing))

        if "representations" not in instance.data:
            instance.data["representations"] = []

        representation = {
            'name': 'ifd',
            'ext': 'ifd',
            'files': files,
            "stagingDir": staging_dir,
            "frameStart": instance.data["frameStart"],
            "frameEnd": instance.data["frameEnd"],
        }
        instance.data["representations"].append(representation)