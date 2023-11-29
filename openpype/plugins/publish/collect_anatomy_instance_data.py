"""
Requires:
    context     -> anatomyData
    context     -> projectEntity
    context     -> assetEntity
    instance    -> asset
    instance    -> subset
    instance    -> family

Optional:
    instance    -> version
    instance    -> resolutionWidth
    instance    -> resolutionHeight
    instance    -> fps

Provides:
    instance    -> projectEntity
    instance    -> assetEntity
    instance    -> anatomyData
    instance    -> version
    instance    -> latestVersion
"""

import copy
import json
import collections

import pyblish.api

from openpype.client import (
    get_assets,
    get_subsets,
    get_last_versions
)
from openpype.pipeline.version_start import get_versioning_start
from openpype.pipeline.latest_version import get_lastest_version_number
from openpype.modules import ModulesManager


class CollectAnatomyInstanceData(pyblish.api.ContextPlugin):
    """Collect Instance specific Anatomy data.

    Plugin is running for all instances on context even not active instances.
    """

    order = pyblish.api.CollectorOrder + 0.49
    label = "Collect Anatomy Instance data"

    follow_workfile_version = False

    def process(self, context):
        self.log.debug("Collecting anatomy data for all instances.")

        project_name = context.data["projectName"]
        self.fill_missing_asset_docs(context, project_name)
        self.fill_latest_versions(context, project_name)
        self.fill_anatomy_data(context)

        self.log.debug("Anatomy Data collection finished.")

    def fill_missing_asset_docs(self, context, project_name):
        self.log.debug("Querying asset documents for instances.")

        context_asset_doc = context.data.get("assetEntity")

        instances_with_missing_asset_doc = collections.defaultdict(list)
        for instance in context:
            instance_asset_doc = instance.data.get("assetEntity")
            _asset_name = instance.data["asset"]

            # There is possibility that assetEntity on instance is already set
            # which can happen in standalone publisher
            if (
                instance_asset_doc
                and instance_asset_doc["name"] == _asset_name
            ):
                continue

            # Check if asset name is the same as what is in context
            # - they may be different, e.g. in NukeStudio
            if context_asset_doc and context_asset_doc["name"] == _asset_name:
                instance.data["assetEntity"] = context_asset_doc

            else:
                instances_with_missing_asset_doc[_asset_name].append(instance)

        if not instances_with_missing_asset_doc:
            self.log.debug("All instances already had right asset document.")
            return

        asset_names = list(instances_with_missing_asset_doc.keys())
        self.log.debug("Querying asset documents with names: {}".format(
            ", ".join(["\"{}\"".format(name) for name in asset_names])
        ))

        asset_docs = get_assets(project_name, asset_names=asset_names)
        asset_docs_by_name = {
            asset_doc["name"]: asset_doc
            for asset_doc in asset_docs
        }

        not_found_asset_names = []
        for asset_name, instances in instances_with_missing_asset_doc.items():
            asset_doc = asset_docs_by_name.get(asset_name)
            if not asset_doc:
                not_found_asset_names.append(asset_name)
                continue

            for _instance in instances:
                _instance.data["assetEntity"] = asset_doc

        if not_found_asset_names:
            joined_asset_names = ", ".join(
                ["\"{}\"".format(name) for name in not_found_asset_names]
            )
            self.log.warning((
                "Not found asset documents with names \"{}\"."
            ).format(joined_asset_names))

    def fill_latest_versions(self, context, project_name):
        """Try to find latest version for each instance's subset.

        Key "latestVersion" is always set to latest version or `None`.

        Args:
            context (pyblish.Context)

        Returns:
            None

        """
        self.log.debug("Querying latest versions for instances.")

        hierarchy = {}
        names_by_asset_ids = collections.defaultdict(set)
        for instance in context:
            # Make sure `"latestVersion"` key is set
            latest_version = instance.data.get("latestVersion")
            instance.data["latestVersion"] = latest_version

            # Skip instances without "assetEntity"
            asset_doc = instance.data.get("assetEntity")
            if not asset_doc:
                continue

            # Store asset ids and subset names for queries
            asset_id = asset_doc["_id"]
            subset_name = instance.data["subset"]

            # Prepare instance hierarchy for faster filling latest versions
            if asset_id not in hierarchy:
                hierarchy[asset_id] = {}
            if subset_name not in hierarchy[asset_id]:
                hierarchy[asset_id][subset_name] = []
            hierarchy[asset_id][subset_name].append(instance)
            names_by_asset_ids[asset_id].add(subset_name)

        subset_docs = []
        if names_by_asset_ids:
            subset_docs = list(get_subsets(
                project_name, names_by_asset_ids=names_by_asset_ids
            ))

        subset_ids = [
            subset_doc["_id"]
            for subset_doc in subset_docs
        ]

        last_version_docs_by_subset_id = get_last_versions(
            project_name, subset_ids, fields=["name"]
        )
        for subset_doc in subset_docs:
            subset_id = subset_doc["_id"]
            last_version_doc = last_version_docs_by_subset_id.get(subset_id)
            if last_version_doc is None:
                continue

            asset_id = subset_doc["parent"]
            subset_name = subset_doc["name"]
            _instances = hierarchy[asset_id][subset_name]
            for _instance in _instances:
                _instance.data["latestVersion"] = last_version_doc["name"]

    def fill_anatomy_data(self, context):
        self.log.debug("Storing anatomy data to instance data.")

        project_doc = context.data["projectEntity"]
        context_asset_doc = context.data.get("assetEntity")

        project_task_types = project_doc["config"]["tasks"]

        for instance in context:
            anatomy_updates = {
                "asset": instance.data["asset"],
                "folder": {
                    "name": instance.data["asset"],
                },
                "family": instance.data["family"],
                "subset": instance.data["subset"],
            }

            # Hierarchy
            asset_doc = instance.data.get("assetEntity")
            if (
                asset_doc
                and (
                    not context_asset_doc
                    or asset_doc["_id"] != context_asset_doc["_id"]
                )
            ):
                parents = asset_doc["data"].get("parents") or list()
                parent_name = project_doc["name"]
                if parents:
                    parent_name = parents[-1]
                anatomy_updates["hierarchy"] = "/".join(parents)
                anatomy_updates["parent"] = parent_name

            # Task
            task_type = None
            task_name = instance.data.get("task")
            if task_name:
                asset_tasks = asset_doc["data"]["tasks"]
                task_type = asset_tasks.get(task_name, {}).get("type")
                task_code = (
                    project_task_types
                    .get(task_type, {})
                    .get("short_name")
                )
                anatomy_updates["task"] = {
                    "name": task_name,
                    "type": task_type,
                    "short": task_code
                }

            # Define version
            if self.follow_workfile_version:
                version_number = context.data('version')
            else:
                version_number = instance.data.get("version")

            # use latest version (+1) if already any exist
            if version_number is None:
                latest_version = instance.data["latestVersion"]
                if latest_version is not None:
                    version_number = int(latest_version) + 1

            version_number = self.get_lastest_version_number(instance)

            # If version is not specified for instance or context
            if version_number is None:
                version_number = get_versioning_start(
                    context.data["projectName"],
                    instance.context.data["hostName"],
                    task_name=task_name,
                    task_type=task_type,
                    family=instance.data["family"],
                    subset=instance.data["subset"]
                )
            anatomy_updates["version"] = version_number

            # Additional data
            resolution_width = instance.data.get("resolutionWidth")
            if resolution_width:
                anatomy_updates["resolution_width"] = resolution_width

            resolution_height = instance.data.get("resolutionHeight")
            if resolution_height:
                anatomy_updates["resolution_height"] = resolution_height

            pixel_aspect = instance.data.get("pixelAspect")
            if pixel_aspect:
                anatomy_updates["pixel_aspect"] = float(
                    "{:0.2f}".format(float(pixel_aspect))
                )

            fps = instance.data.get("fps")
            if fps:
                anatomy_updates["fps"] = float("{:0.2f}".format(float(fps)))

            anatomy_data = copy.deepcopy(context.data["anatomyData"])
            anatomy_data.update(anatomy_updates)

            # Store anatomy data
            instance.data["projectEntity"] = project_doc
            instance.data["anatomyData"] = anatomy_data
            instance.data["version"] = version_number

            # Log collected data
            instance_name = instance.data["name"]
            instance_label = instance.data.get("label")
            if instance_label:
                instance_name += " ({})".format(instance_label)
            self.log.debug("Anatomy data for instance {}: {}".format(
                instance_name,
                json.dumps(anatomy_data, indent=4)
            ))

    def get_lastest_version_number(self, instance):
        """Delete version on ftrack.

        Handling of ftrack logic in this plugin is not ideal. But in OP3 it is
        almost impossible to solve the issue other way.

        Note:
            Asset versions on ftrack are not deleted but marked as
                "not published" which cause that they're invisible.

        Args:
            data (dict): Data sent to subset loader with full context.
        """
        self.log.debug("#" * 50)
        # First check for ftrack id on asset document
        #   - skip if ther is none

        # if instance.data['name'] == "renderLightMasterLayer":
        #     self.log.debug(f"ASSET: {instance.data['asset']}")
        #     self.log.debug(f"ID: {instance.data['id']}")
        #     self.log.debug(f"RENDER_LAYER: {instance.data['renderlayer']}")
        #     self.log.debug(f"INSTANCE_ID: {instance.data['instance_id']}")
        #     self.log.debug(f"ASSET_ENTITY: {instance.data['assetEntity']}")
        #     self.log.debug(f"LATEST_VERSION: {instance.data['latestVersion']}")
        asset_ftrack_id = instance.data["assetEntity"]["data"].get("ftrackId")
        self.log.debug(f"ASSET_FTRACK_ID: {asset_ftrack_id}")

        if not asset_ftrack_id:
            self.log.info((
                "Asset does not have filled ftrack id. Skipped getting"
                " ftrack latest version."
            ))
            return

        # Check if ftrack module is enabled
        modules_manager = ModulesManager()
        ftrack_module = modules_manager.modules_by_name.get("ftrack")
        if not ftrack_module or not ftrack_module.enabled:
            return
        self.log.debug("FTRACK MODULE ENABLED")
        import ftrack_api

        session = ftrack_api.Session()
        subset_name = instance.data["subset"]
        self.log.debug(f"SUBSET_NAME: {subset_name}")
        # self.log.debug(f"VERSIONS: {instance.data['versions']}")
        # versions = {
        #     '"{}"'.format(version_doc["name"])
        #     for version_doc in instance["versions"]
        # }
        # asset_versions = session.query(
        #     (
        #         "select id, is_published from AssetVersion where"
        #         " asset.parent.id is \"{}\""
        #         " and asset.name is \"{}\""
        #         # " and version in ({})"
        #     ).format(
        #         asset_ftrack_id,
        #         subset_name,
        #         # ",".join(versions)
        #     )
        # ).all()
        asset_versions = session.query(
            "select id, name, versions, latest_version from Asset where"
            f" id is '{asset_ftrack_id}'"
        ).all()

        # # Set attribute `is_published` to `False` on ftrack AssetVersions
        for asset_version in asset_versions:
            for version in asset_version['versions']:
                self.log.debug(f"VERSION: {version}")
                asset_query = session.query(
                    "select id, version from AssetVersion where"
                    f" id is '{version['id']}'"
                ).all()
                for a in asset_query:
                    self.log.debug(f"ASSET_QUERY: {a['version']}")
        #     asset_version["is_published"] = False

        # try:
        #     session.commit()

        # except Exception:
        #     msg = (
        #         "Could not set `is_published` attribute to `False`"
        #         " for selected AssetVersions."
        #     )
        #     log.error(msg)
