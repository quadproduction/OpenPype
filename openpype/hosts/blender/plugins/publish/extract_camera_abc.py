import os
import json
import bpy

from openpype.pipeline import publish
from openpype.hosts.blender.api import plugin
from openpype.hosts.blender.api.pipeline import AVALON_PROPERTY


class ExtractCameraABC(publish.Extractor):
    """Extract camera as ABC."""

    label = "Extract Camera (ABC)"
    hosts = ["blender"]
    families = ["camera"]
    optional = True

    def process(self, instance):
        # Define extract output file path
        stagingdir = self.staging_dir(instance)
        filename = f"{instance.name}.abc"
        filepath = os.path.join(stagingdir, filename)
        jsonname = f"{instance.name}.json"
        json_path = os.path.join(stagingdir, jsonname)

        # Perform extraction
        self.log.info("Performing extraction..")

        plugin.deselect_all()

        asset_group = None
        for obj in instance:
            if obj.get(AVALON_PROPERTY):
                asset_group = obj
                break
        assert asset_group, "No asset group found"

        # Need to cast to list because children is a tuple
        selected = list(asset_group.children)

        if not selected:
            self.log.error("Extraction failed: No child objects found in the asset group.")
            return

        active = selected[0]

        camera = None
        for obj in selected:
            if obj.type == "CAMERA":
                camera = (obj.data)
            obj.select_set(True)

        # Create focal value dict throught time for blender
        if camera:
            camera_data_dict = {"focal_data": {}}
            # save current frame to reset it after the dict creation
            currentframe = bpy.context.scene.frame_current

            for frame in range (bpy.context.scene.frame_start, (bpy.context.scene.frame_end+1)):
                bpy.context.scene.frame_set(frame)
                camera_data_dict["focal_data"][frame] = camera.lens

            # reset old current frame
            bpy.context.scene.frame_set(currentframe)

            # Performe json extraction
            # Serializing json
            json_object = json.dumps(camera_data_dict, indent=4)

            # Writing to json
            with open(json_path, "w") as outfile:
                outfile.write(json_object)

        context = plugin.create_blender_context(
            active=active, selected=selected)

        with bpy.context.temp_override(**context):
            # We export the abc
            bpy.ops.wm.alembic_export(
                filepath=filepath,
                selected=True,
                flatten=True
            )

        plugin.deselect_all()

        if "representations" not in instance.data:
            instance.data["representations"] = []

        representation = {
            'name': 'abc',
            'ext': 'abc',
            'files': filename,
            "stagingDir": stagingdir,
        }
        instance.data["representations"].append(representation)

        json_representation = {
            'name': 'jsonCam',
            'ext': 'json',
            'files': jsonname,
            "stagingDir": stagingdir,
        }
        instance.data["representations"].append(json_representation)

        self.log.info("Extracted instance '%s' to: %s\nExtracted instance '%s' to: %s",
                      instance.name, representation, jsonname, json_representation)
