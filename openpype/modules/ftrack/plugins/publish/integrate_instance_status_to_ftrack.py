import sys
import six
from pathlib import Path

import pyblish.api

from openpype.settings import get_current_project_settings
from openpype.modules.ftrack import get_asset_version_by_task_id


class IntegrateInstanceStatusToFtrack(pyblish.api.InstancePlugin):

    order = pyblish.api.IntegratorOrder + 0.4999
    label = "Integrate Instance Status To Ftrack"
    families = ["ftrack"]
    active = True

    def process(self, instance):
        self.log.debug(f"SATUTS_TO_SET: {instance.data['creator_attributes'].get('ftrack_status')}")

        task = instance.data.get("ftrackTask")
        name = instance.data.get("name")
        session = instance.context.data["ftrackSession"]

        # Check if there are any integrated AssetVersion entities
        asset_versions_key = "ftrackIntegratedAssetVersionsData"
        asset_versions_key_backwards_compatible = "ftrackIntegratedAssetVersionsData"  # noqa
        asset_version_data = instance.data.get(
            asset_versions_key
        ) or instance.data.get(asset_versions_key_backwards_compatible)
        if not asset_version_data:
            asset_version_data = get_asset_version_by_task_id(
                session,
                task['id'],
                name
            )
        else:
            for asset_version in asset_version_data.values():
                asset_version_data = asset_version["asset_version"]

        if not asset_version_data:
            self.log.debug("No AssetVersion found")
            return

        instance_status = instance.data['creator_attributes'].get(
            'ftrack_status'
        )
        asset_version_data["status"] = instance_status

        try:
            # session.commit()
            self.log.debug(
                "Status set to {} for AssetVersion \"{}\" ".format(
                    instance_status, str(asset_version_data)
                )
            )
        except Exception:
            tp, value, tb = sys.exc_info()
            session.rollback()
            session._configure_locations()
            six.reraise(tp, value, tb)
