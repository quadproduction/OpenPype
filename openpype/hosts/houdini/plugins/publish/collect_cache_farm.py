import os
import pyblish.api
import hou
from openpype.hosts.houdini.api import lib, colorspace
from openpype.hosts.houdini.api.lib import get_color_management_preferences
from openpype.settings import get_project_settings


class CollectDataforCache(pyblish.api.InstancePlugin):
    """Collect data for caching to Deadline."""

    order = pyblish.api.CollectorOrder + 0.1
    families = ["ass", "abc",
                "vdbcache", "mantraifd",
                "redshiftproxy", "bgeo"]
    hosts = ["houdini"]
    targets = ["local", "remote"]
    label = "Collect Data for Cache"

    def process(self, instance):
        if instance.data.get("farm"):
            for family in instance.data["families"]:
                instance.data["family"] = family
                instance.data["subset"] = instance.name
            # instance.data["expected_families"]
            # only created for farm caching
            instance.data["families"] = list()
            instance.data["families"].append(instance.data["family"])
            instance.data["expected_families"] = list()
            instance.data["expected_families"].extend(
                instance.data["families"])
            instance.data["families"].append("publish.hou")
            data = dict()
            data["chunkSize"] = 999999
            data["plugin"] = "Houdini"
            data["publish"] = True
            ropnode = hou.node(instance.data["instance_node"])
            instance.data.update(data)
            output_parm = lib.get_output_parameter(ropnode)
            # TODO: make sure the expectedfiles include all the data
            expected_filepath = output_parm.eval()
            if "files" not in instance.data:
                instance.data["files"] = list()
            if "expectedFiles" not in instance.data:
                instance.data["expectedFiles"] = list()
            cache_files = dict()
            if instance.data.get("frames"):
                files = self.get_files(
                    instance, expected_filepath)
                # list of files
                instance.data["files"].extend(files)
            else:
                instance.data["files"].append(output_parm.eval())
            cache_files = {"_": instance.data["files"]}
            instance.data["expectedFiles"].append(cache_files)

            project_name = instance.context.data["projectName"]
            settings = get_project_settings(project_name)
            # use setting for publish job on farm, no reason to have it separately
            primary_pool = (settings["deadline"]["publish"]["CollectDeadlinePools"]["primary_pool"])
            instance.data["primaryPool"] = primary_pool
            secondary_pool = (settings["deadline"]["publish"]["CollectDeadlinePools"]["secondary_pool"])
            instance.data["secondaryPool"] = secondary_pool

            instance.data["attachTo"] = []      # stub required data

            # update the colorspace data
            
            colorspace_data = get_color_management_preferences()
            instance.data["renderProducts"] = colorspace.ARenderProduct()
            instance.data["colorspaceConfig"] = colorspace_data["config"]
            instance.data["colorspaceDisplay"] = colorspace_data["display"]
            instance.data["colorspaceView"] = colorspace_data["view"]
            self.log.debug("{}".format(instance.data))
            
        else:
            self.log.debug("Caching at farm disabled!")

    def get_files(self, instance, output_parm):
        """Get the files with the frame range data

        Args:
            instance (_type_): instance
            output_parm (_type_): path of output parameter

        Returns:
            files: a list of files
        """
        files = []
        directory = os.path.dirname(output_parm)
        frames = instance.data["frames"]

        for frame in frames:
            file = os.path.join(directory, frame)
            file = file.replace("\\", "/")
            files.append(file)

        return files
    
    