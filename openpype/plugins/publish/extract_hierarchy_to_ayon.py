import collections
import copy
import json
import uuid
import pyblish.api

from ayon_api import slugify_string
from ayon_api.entity_hub import EntityHub

from openpype import AYON_SERVER_ENABLED


def _default_json_parse(value):
    return str(value)


class ExtractHierarchyToAYON(pyblish.api.ContextPlugin):
    """Create entities in AYON based on collected data."""

    order = pyblish.api.ExtractorOrder - 0.01
    label = "Extract Hierarchy To AYON"
    families = ["clip", "shot"]

    def process(self, context):
        if not AYON_SERVER_ENABLED:
            return

        hierarchy_context = context.data.get("hierarchyContext")
        if not hierarchy_context:
            self.log.info("Skipping")
            return

        project_name = context.data["projectName"]
        hierarchy_context = self._filter_hierarchy(context)
        if not hierarchy_context:
            self.log.info("All folders were filtered out")
            return

        self.log.debug("Hierarchy_context: {}".format(
            json.dumps(hierarchy_context, default=_default_json_parse)
        ))

        entity_hub = EntityHub(project_name)
        project = entity_hub.project_entity

        hierarchy_match_queue = collections.deque()
        hierarchy_match_queue.append((project, hierarchy_context))
        while hierarchy_match_queue:
            item = hierarchy_match_queue.popleft()
            entity, entity_info = item

            # Update attributes of entities
            for attr_name, attr_value in entity_info["attributes"].items():
                if attr_name in entity.attribs:
                    entity.attribs[attr_name] = attr_value

            # Check if info has any children to sync
            children_info = entity_info["children"]
            tasks_info = entity_info["tasks"]
            if not tasks_info and not children_info:
                continue

            # Prepare children by lowered name to easily find matching entities
            children_by_low_name = {
                child.name.lower(): child
                for child in entity.children
            }

            # Create tasks if are not available
            for task_info in tasks_info:
                task_label = task_info["name"]
                task_name = slugify_string(task_label)
                if task_name == task_label:
                    task_label = None
                task_entity = children_by_low_name.get(task_name.lower())
                # TODO propagate updates of tasks if there are any
                # TODO check if existing entity have 'task' type
                if task_entity is None:
                    task_entity = entity_hub.add_new_task(
                        task_info["type"],
                        parent_id=entity.id,
                        name=task_name
                    )

                if task_label:
                    task_entity.label = task_label

            # Create/Update sub-folders
            for child_info in children_info:
                child_label = child_info["name"]
                child_name = slugify_string(child_label)
                if child_name == child_label:
                    child_label = None
                # TODO check if existing entity have 'folder' type
                child_entity = children_by_low_name.get(child_name.lower())
                if child_entity is None:
                    child_entity = entity_hub.add_new_folder(
                        child_info["entity_type"],
                        parent_id=entity.id,
                        name=child_name
                    )

                if child_label:
                    child_entity.label = child_label

                # Add folder to queue
                hierarchy_match_queue.append((child_entity, child_info))

        entity_hub.commit_changes()

    def _filter_hierarchy(self, context):
        """Filter hierarchy context by active folder names.

        Hierarchy context is filtered to folder names on active instances.

        Change hierarchy context to unified structure which suits logic in
        entity creation.

        Output example:
            {
                "name": "MyProject",
                "entity_type": "Project",
                "attributes": {},
                "tasks": [],
                "children": [
                    {
                        "name": "seq_01",
                        "entity_type": "Sequence",
                        "attributes": {},
                        "tasks": [],
                        "children": [
                            ...
                        ]
                    },
                    ...
                ]
            }

        Todos:
            Change how active folder are defined (names won't be enough in
                AYON).

        Args:
            context (pyblish.api.Context): Pyblish context.

        Returns:
            dict[str, Any]: Hierarchy structure filtered by folder names.
        """

        # filter only the active publishing instances
        active_folder_names = set()
        for instance in context:
            if instance.data.get("publish") is not False:
                active_folder_names.add(instance.data.get("asset"))

        active_folder_names.discard(None)

        self.log.debug("Active folder names: {}".format(active_folder_names))
        if not active_folder_names:
            return None

        project_item = None
        project_children_context = None
        for key, value in context.data["hierarchyContext"].items():
            project_item = copy.deepcopy(value)
            project_children_context = project_item.pop("childs", None)
            project_item["name"] = key
            project_item["tasks"] = []
            project_item["attributes"] = project_item.pop(
                "custom_attributes", {}
            )
            project_item["children"] = []

        if not project_children_context:
            return None

        project_id = uuid.uuid4().hex
        items_by_id = {project_id: project_item}
        parent_id_by_item_id = {project_id: None}
        valid_ids = set()

        hierarchy_queue = collections.deque()
        hierarchy_queue.append((project_id, project_children_context))
        while hierarchy_queue:
            queue_item = hierarchy_queue.popleft()
            parent_id, children_context = queue_item
            if not children_context:
                continue

            for asset_name, asset_info in children_context.items():
                if (
                    asset_name not in active_folder_names
                    and not asset_info.get("childs")
                ):
                    continue
                item_id = uuid.uuid4().hex
                new_item = copy.deepcopy(asset_info)
                new_item["name"] = asset_name
                new_item["children"] = []
                new_children_context = new_item.pop("childs", None)
                tasks = new_item.pop("tasks", {})
                task_items = []
                for task_name, task_info in tasks.items():
                    task_info["name"] = task_name
                    task_items.append(task_info)
                new_item["tasks"] = task_items
                new_item["attributes"] = new_item.pop("custom_attributes", {})

                items_by_id[item_id] = new_item
                parent_id_by_item_id[item_id] = parent_id

                if asset_name in active_folder_names:
                    valid_ids.add(item_id)
                hierarchy_queue.append((item_id, new_children_context))

        if not valid_ids:
            return None

        for item_id in set(valid_ids):
            parent_id = parent_id_by_item_id[item_id]
            while parent_id is not None and parent_id not in valid_ids:
                valid_ids.add(parent_id)
                parent_id = parent_id_by_item_id[parent_id]

        valid_ids.discard(project_id)
        for item_id in valid_ids:
            parent_id = parent_id_by_item_id[item_id]
            item = items_by_id[item_id]
            parent_item = items_by_id[parent_id]
            parent_item["children"].append(item)

        if not project_item["children"]:
            return None
        return project_item
