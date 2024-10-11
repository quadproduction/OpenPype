import os
import bpy

import pyblish.api
from openpype.pipeline import get_current_task_name, get_current_asset_name, get_current_project_name
from openpype.pipeline.create.subset_name import get_subset_name
from openpype.client.mongo.entities import get_asset_by_name
from openpype.hosts.blender.api import workio


class SaveWorkfiledAction(pyblish.api.Action):
    """Save Workfile."""
    label = "Save Workfile"
    on = "failed"
    icon = "save"

    def process(self, context, plugin):
        bpy.ops.wm.avalon_workfiles()


class CollectBlenderCurrentFile(pyblish.api.ContextPlugin):
    """Inject the current working file into context"""

    order = pyblish.api.CollectorOrder - 0.5
    label = "Blender Current File"
    hosts = ["blender"]
    actions = [SaveWorkfiledAction]
    default_variant = "Main"

    def process(self, context):
        """Inject the current working file"""
        current_file = workio.current_file()

        context.data["currentFile"] = current_file

        variant = self.default_variant

        assert current_file, (
            "Current file is empty. Save the file before continuing."
        )

        folder, file = os.path.split(current_file)
        filename, ext = os.path.splitext(file)

        task = get_current_task_name()
        asset_doc = get_asset_by_name(
                get_current_project_name(), get_current_asset_name()
            )

        data = {}

        # create instance
        instance = context.create_instance(name=filename)

        # Retrieve subset from settings and no longer hardcoded
        subset = get_subset_name(
                "workfile",
                variant,
                task,
                asset_doc
        )

        data.update({
            "subset": subset,
            "asset": get_current_asset_name(),
            "label": subset,
            "publish": True,
            "family": "workfile",
            "families": ["workfile"],
            "setMembers": [current_file],
            "frameStart": bpy.context.scene.frame_start,
            "frameEnd": bpy.context.scene.frame_end,
        })

        data["representations"] = [{
            "name": ext.lstrip("."),
            "ext": ext.lstrip("."),
            "files": file,
            "stagingDir": folder,
        }]

        instance.data.update(data)

        self.log.info("Collected instance: {}".format(file))
        self.log.info("Scene path: {}".format(current_file))
        self.log.info("staging Dir: {}".format(folder))
        self.log.info("subset: {}".format(subset))
