from maya import cmds

import pyblish.api
import openpype.api
import openpype.hosts.maya.api.action


class ValidateNodeNoLocked(pyblish.api.InstancePlugin):
    """Ensure there is no locked node."""

    order = openpype.api.ValidateContentsOrder
    hosts = ['maya']
    families = ['model']
    label = "No Locked nodes"
    actions = [openpype.api.RepairAction,
               openpype.hosts.maya.api.action.SelectInvalidAction]

    @classmethod
    def get_invalid(cls, instance):
        locked_nodes = cmds.ls(instance, long=True, lockedNodes=True)
        invalid = []

        for node in locked_nodes:
            invalid.append(node)

        return invalid

    def process(self, instance):
        invalid = self.get_invalid(instance)

        if invalid:
            raise ValueError("Locked nodes found: "
                             "{0}".format(invalid))

    @classmethod
    def repair(cls, instance):
        """Unlock locked nodes."""

        invalid = cls.get_invalid(instance)

        cmds.lockNode(invalid, lock=False)
        for node in invalid:
            if cmds.nodeType(node) == "camera":
                cmds.camera(node, edit=True, startupCamera=False)
