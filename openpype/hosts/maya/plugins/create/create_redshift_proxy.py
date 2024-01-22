# -*- coding: utf-8 -*-
"""Creator of Redshift proxy subset types."""

from openpype.hosts.maya.api import plugin, lib
from openpype.lib import (
    BoolDef,
    EnumDef
)
from openpype.pipeline.context_tools import get_current_project_name
from openpype.modules.ftrack.lib import get_ftrack_statuses


class CreateRedshiftProxy(plugin.MayaCreator):
    """Create instance of Redshift Proxy subset."""

    identifier = "io.openpype.creators.maya.redshiftproxy"
    label = "Redshift Proxy"
    family = "redshiftproxy"
    icon = "gears"

    def get_instance_attr_defs(self):
        project_name = get_current_project_name()
        statuses = get_ftrack_statuses(project_name)
        statuses = sorted([status['name'] for status in statuses])

        defs = [
            BoolDef("animation",
                    label="Export animation",
                    default=False),
        ]

        defs.extend(lib.collect_animation_defs())
        defs.extend([
            EnumDef("ftrackStatus",
                    label="Ftrack Status",
                    items=statuses,
                    default="In progress"),
        ])
        return defs
