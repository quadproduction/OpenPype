# -*- coding: utf-8 -*-
import pyblish.api
from openpype.pipeline import PublishValidationError
from openpype.pipeline.publish import RepairAction

import hou


class SelectInvalidAction(RepairAction):
    label = "Select Invalid ROP"
    icon = "mdi.cursor-default-click"

class ValidateSopOutputNode(pyblish.api.InstancePlugin):
    """Validate the instance SOP Output Node.

    This will ensure:
        - The SOP Path is set.
        - The SOP Path refers to an existing object.
        - The SOP Path node is a SOP node.
        - The SOP Path node has at least one input connection (has an input)
        - The SOP Path has geometry data.

    """

    order = pyblish.api.ValidatorOrder
    families = ["pointcache", "vdbcache"]
    hosts = ["houdini"]
    label = "Validate Output Node"
    actions = [SelectInvalidAction]

    def process(self, instance):

        invalid = self.get_invalid(instance)
        if invalid:
            raise PublishValidationError(
                "Output node(s) are incorrect",
                title="Invalid output node(s)"
            )

    @classmethod
    def get_invalid(cls, instance):
        output_node = instance.data.get("output_node")

        if output_node is None:
            node = hou.node(instance.data["instance_node"])
            cls.log.error(
                "SOP Output node in '%s' does not exist. "
                "Ensure a valid SOP output path is set." % node.path()
            )

            return [node.path()]

        # Output node must be a Sop node.
        if not isinstance(output_node, hou.SopNode):
            cls.log.error(
                "Output node %s is not a SOP node. "
                "SOP Path must point to a SOP node, "
                "instead found category type: %s"
                % (output_node.path(), output_node.type().category().name())
            )
            return [output_node.path()]

        # For the sake of completeness also assert the category type
        # is Sop to avoid potential edge case scenarios even though
        # the isinstance check above should be stricter than this category
        if output_node.type().category().name() != "Sop":
            raise PublishValidationError(
                ("Output node {} is not of category Sop. "
                 "This is a bug.").format(output_node.path()),
                title=cls.label)

        # Ensure the node is cooked and succeeds to cook so we can correctly
        # check for its geometry data.
        if output_node.needsToCook():
            cls.log.debug("Cooking node: %s" % output_node.path())
            try:
                output_node.cook()
            except hou.Error as exc:
                cls.log.error("Cook failed: %s" % exc)
                cls.log.error(output_node.errors()[0])
                return [output_node.path()]

        # Ensure the output node has at least Geometry data
        if not output_node.geometry():
            cls.log.error(
                "Output node `%s` has no geometry data." % output_node.path()
            )
            return [output_node.path()]

    @classmethod
    def repair(cls, instance):
        """Select Invalid ROP.

        It's used to select invalid ROP which tells the
        artist which ROP node need to be fixed!
        """

        rop_node = hou.node(instance.data["instance_node"])
        rop_node.setSelected(True, clear_all_selected=True)

        cls.log.debug(
            '%s has been selected'
            % rop_node.path()
        )
