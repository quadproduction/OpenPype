import json
from pathlib import Path

import bpy

from openpype.client.mongo.entities import get_project
from openpype.pipeline import registered_host

from .workfile_template_resolving import (
    get_resolved_name,
    get_entity_prefix
)
from .workio import (
    current_file,
    save_file
)
from openpype.pipeline.template_data import get_template_data

from openpype.pipeline.workfile.workfile_template_builder import (
    TemplateAlreadyImported,
    AbstractTemplateBuilder,
    PlaceholderPlugin,
    LoadPlaceholderItem,
    CreatePlaceholderItem,
    PlaceholderLoadMixin,
    PlaceholderCreateMixin
)

from .lib import (
    read,
    imprint,
    get_selection,
    get_active_collection,
    make_scene_empty,
    #is_collection_in_collection,
    get_object_parent_collections
)

AVALON_PLACEHOLDER = "AVALON_PLACEHOLDER"

class BlenderTemplateBuilder(AbstractTemplateBuilder):
    """Concrete implementation of AbstractTemplateBuilder for blender"""

    use_legacy_creators = True

    def import_template(self, path):
        """Import template into current scene.
        Block if a template is already loaded.

        Args:
            path (str): A path to current template (usually given by
            get_template_preset implementation)

        Returns:
            bool: Whether the template was successfully imported or not
        """
        # Cancel if template alreday imported
        for scene in bpy.data.scenes:
            if scene.name == self.current_asset_name:
                raise TemplateAlreadyImported((
                    "Build template already loaded\n"
                    "Clean scene if needed (File > New Scene)"
                ))

        # Generate template data for name resolving
        self.template_data = get_template_data(
                                get_project(self.project_name),
                                self.current_asset_doc,
                                self.current_task_name,
                                self.host_name
                            )

        # Empty and clean current scene
        make_scene_empty()

        # Prepare all Collection to Append from template and retrieve the instanced ones.
        path = Path(path)

        # Get the collections to append from template .blend
        tpl_element_names = self._get_elements_to_append(path)

        # Create a new scene and delete others.
        bpy.ops.scene.new(type='EMPTY')
        bpy.context.scene.name = self.current_asset_name
        for scene in bpy.data.scenes:
            if scene.name == self.current_asset_name:
                continue
            # Remove scene.
            bpy.data.scenes.remove(scene, do_unlink=True)

        # Append Template Elements
        for element_type, element_names in tpl_element_names.items():
            directory = path.joinpath(element_type)
            for ele_name in element_names:
                # security to avoid appending twice the same collection
                # in case one collection is in a already imported collection
                if ele_name in bpy.data.collections.keys():
                    continue
                filepath = directory.joinpath(ele_name)
                filename = ele_name
                bpy.ops.wm.append(filepath=str(filepath), filename=filename, directory=str(directory),
                instance_object_data=True, use_recursive=True)

        # Make the append world active
        world = bpy.data.worlds.get(tpl_element_names["World"][0])
        if world:
            bpy.context.scene.world = world

        # Make the camera active
        cameras = [cam for cam in bpy.data.objects.values() if cam.type == 'CAMERA']
        if cameras:
            bpy.context.scene.camera = cameras[0]

        # Once the collection are append, clean local unsued
        # will remove camera/light/mesh from default scene
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)

        # clean the linked library
        for lib in bpy.data.libraries:
            bpy.data.libraries.remove(lib, do_unlink=True)

        # Resolve the template collections' names in .blend
        self._rename_template_collections()

        # Save file
        save_file(current_file())
        return True

    def _rename_template_collections(self):
        """Creating or renaming collection to complete the template build

        Returns:
            dict: {str: bpy.data.colletion}
                    A dict associating type_collection_matcher to the blender coll
        """
        # Retrieve short name for entity_type from settings:
        entity_type_short = get_entity_prefix(self.template_data)

        if entity_type_short:
            self.template_data["parent"] = entity_type_short

        for coll in bpy.data.collections.values():
            resolved_name = get_resolved_name(self.template_data, coll.name)
            if resolved_name != coll.name:
                coll.name = resolved_name

    @staticmethod
    def _get_elements_to_append(path):
        """List all elements to append in scene based on a templated .blend
        Will avoid the instanced collections or collections in collections.

        Args:
            path (Path): A path to current template
        Returns:
            dict: {str: list}
                A dict of element type associated to a list of names to append
        """
        return_dict = {}
        # Load the libraries from template.blend
        with bpy.data.libraries.load(str(path), link=True) as (data_from, data_to):
            data_to.objects = data_from.objects
            data_collections = data_from.collections
            data_worlds = data_from.worlds

        # Start the search for instanced collections
        instanced_collections_names = set()

        # Access to objects properties
        for obj in data_to.objects:
            # Stock instanced collections
            if obj.instance_type == 'COLLECTION' and obj.instance_collection:
                print(f"The collection {obj.instance_collection.name} is instanced in {obj.name}")
                instanced_collections_names.add(obj.instance_collection.name)
            # Delete linked objects
            bpy.data.objects.remove(obj)

        # Once the collection to append are saved, clean unsued linked data
        bpy.ops.outliner.orphans_purge(do_local_ids=False, do_linked_ids=True, do_recursive=False)

        # Return the collections to append if not instanced
        return_dict["Collection"] = [coll_name for coll_name in data_collections if coll_name not in instanced_collections_names]
        return_dict["World"] = data_worlds

        return return_dict


class BlenderPlaceholderLoadPlugin(PlaceholderPlugin, PlaceholderLoadMixin):
    identifier = "blender.load"
    label = "Blender Load"

    def _collect_scene_placeholders(self):
        # Cache placeholder data to shared data
        placeholder_nodes = self.builder.get_shared_populate_data(
            "placeholder_nodes"
        )
        if placeholder_nodes is None:
            from .pipeline import AVALON_PROPERTY
            empties = [obj for obj in bpy.data.objects if obj.get(AVALON_PROPERTY, {}).get("plugin_identifier", None)]
            placeholder_nodes = {}
            for empty in empties:
                node_name = empty.name
                placeholder_nodes[node_name] = (
                    self._parse_placeholder_node_data(empty)
                )

            self.builder.set_shared_populate_data(
                "placeholder_nodes", placeholder_nodes
            )
        return placeholder_nodes

    def _parse_placeholder_node_data(self, empty):
        placeholder_data = read(empty)
        parent_name = (
            empty.get("parent")
            or ""
        )

        placeholder_data.update({
            "parent": parent_name,
        })
        return placeholder_data

    def _create_placeholder_name(self, placeholder_data):
        placeholder_name_parts = placeholder_data["builder_type"].split("_")
        pos = 1
        # add family in any
        placeholder_family = placeholder_data["family"]
        if placeholder_family:
            placeholder_name_parts.insert(pos, placeholder_family)
            pos += 1

        # add loader arguments if any
        loader_args = placeholder_data["loader_args"]
        if loader_args:
            loader_args = json.loads(loader_args.replace('\'', '\"'))
            values = [v for v in loader_args.values()]
            for value in values:
                placeholder_name_parts.insert(str(pos), value)
                pos += 1

        placeholder_name = "_".join(placeholder_name_parts)

        return placeholder_name.capitalize()

    def _get_loaded_repre_ids(self):
        loaded_representation_ids = self.builder.get_shared_populate_data(
            "loaded_representation_ids"
        )
        if loaded_representation_ids is None:
            from .pipeline import AVALON_PROPERTY
            empties = [obj for obj in bpy.data.objects if obj.get(AVALON_PROPERTY, {}).get("representation", None)]
            loaded_representation_ids = {
                empty.get(".representation")
                for empty in empties
            }
            self.builder.set_shared_populate_data(
                "loaded_representation_ids", loaded_representation_ids
            )
        return loaded_representation_ids

    def create_placeholder(self, placeholder_data):

        active_coll = get_active_collection()

        placeholder_data["plugin_identifier"] = self.identifier

        placeholder_name = self._create_placeholder_name(placeholder_data)

        placeholder = bpy.data.objects.new(name=placeholder_name, object_data=None)
        placeholder.empty_display_type = 'SINGLE_ARROW'

        if active_coll:
            active_coll.objects.link(placeholder)
        else:
            bpy.context.scene.collection.children.link(placeholder)

        if placeholder_data.get('action', None) is None:
            placeholder_data.pop('action')

        imprint(placeholder, placeholder_data)

    def update_placeholder(self, placeholder_item, placeholder_data):
        obj = bpy.data.objects.get(placeholder_item.scene_identifier)
        if not obj:
            raise ValueError("No objects found")

        new_values = {}
        for key, value in placeholder_data.items():
            placeholder_value = placeholder_item.data.get(key)
            if value != placeholder_value:
                new_values[key] = value
                placeholder_item.data[key] = value

        placeholder_name = self._create_placeholder_name(placeholder_data)
        obj.name = placeholder_name
        imprint(obj, new_values)

    def collect_placeholders(self):
        output = []
        scene_placeholders = self._collect_scene_placeholders()
        for obj_name, placeholder_data in scene_placeholders.items():
            if placeholder_data.get("plugin_identifier") != self.identifier:
                continue

            output.append(
                LoadPlaceholderItem(obj_name, placeholder_data, self)
            )

        return output

    def populate_placeholder(self, placeholder):
        self.populate_load_placeholder(placeholder)

    def repopulate_placeholder(self, placeholder):
        repre_ids = self._get_loaded_repre_ids()
        self.populate_load_placeholder(placeholder, repre_ids)

    def get_placeholder_options(self, options=None):
        return self.get_load_plugin_options(options)

    def post_placeholder_process(self, placeholder, failed):
        """Add the placehodlers into a dedicated storage collection
        """
        placeholder_coll = bpy.data.collections.get(AVALON_PLACEHOLDER)

        if not placeholder_coll:
            placeholder_coll = bpy.data.collections.new(name=AVALON_PLACEHOLDER)
            bpy.context.scene.collection.children.link(placeholder_coll)

        # Get the corresponding placerholder object in scene
        obj = bpy.data.objects.get(placeholder.scene_identifier)
        if not obj:
            return

        # Get its parent
        parent = get_object_parent_collections(obj)
        if not parent:
            return

        # Unlink from parent and link to storage collection
        parent.objects.unlink(obj)
        placeholder_coll.objects.link(obj)
        # Save file
        save_file(current_file())

    def delete_placeholder(self, placeholder):
        """Remove placeholder if building was successful"""
        obj = bpy.data.objects.get(placeholder.scene_identifier)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

    def load_succeed(self, placeholder, container):
        self._parent_in_hierarchy(placeholder, container)

    def _parent_in_hierarchy(self, placeholder, container):
        """Parent loaded container to placeholder's parent.

        Args:
            container (bpy.data.object): Placeholder loaded containers
        """
        obj = bpy.data.objects.get(placeholder.scene_identifier)
        if not obj:
            raise ValueError("No object found for {}".format(placeholder.scene_identifier))

        parent = get_object_parent_collections(obj)
        if not parent:
            return

        # Link newly imported container to placeholder parent
        parent.objects.link(container)
        # Link newly imported container children to placeholder parent
        for child in container.children:
            parent.objects.link(child)
            bpy.context.scene.collection.objects.unlink(child)

        bpy.context.scene.collection.objects.unlink(container)




class BlenderPlaceholderCreatePlugin(PlaceholderPlugin, PlaceholderCreateMixin):
    identifier = "blender.create"
    label = "Blender Create"

    def _collect_scene_placeholders(self):
        # Cache placeholder data to shared data
        placeholder_nodes = self.builder.get_shared_populate_data(
            "placeholder_nodes"
        )
        if placeholder_nodes is None:
            from .pipeline import AVALON_PROPERTY
            empties = [obj for obj in bpy.data.objects if obj.get(AVALON_PROPERTY, {}).get("plugin_identifier", None)]
            placeholder_nodes = {}
            for empty in empties:
                node_name = empty.name
                placeholder_nodes[node_name] = (
                    self._parse_placeholder_node_data(empty)
                )

            self.builder.set_shared_populate_data(
                "placeholder_nodes", placeholder_nodes
            )
        return placeholder_nodes

    def _parse_placeholder_node_data(self, empty):
        placeholder_data = read(empty)
        parent_name = (
            empty.get("parent")
            or ""
        )

        placeholder_data.update({
            "parent": parent_name,
        })
        return placeholder_data

    def _create_placeholder_name(self, placeholder_data):
        placeholder_name_parts = placeholder_data["create"].split(".")

        pos = 1
        # add family in any
        placeholder_variant = placeholder_data["create_variant"]
        if placeholder_variant:
            placeholder_name_parts.insert(pos, placeholder_variant)
            pos += 1

        placeholder_name = "_".join(placeholder_name_parts)

        return placeholder_name.capitalize()

    def create_placeholder(self, placeholder_data):
        from .pipeline import AVALON_INSTANCES

        # Deselect all
        bpy.ops.object.select_all(action='DESELECT')

        placeholder_data["plugin_identifier"] = self.identifier

        placeholder_name = self._create_placeholder_name(placeholder_data)

        instances = bpy.data.collections.get(AVALON_INSTANCES)
        if not instances:
            instances = bpy.data.collections.new(name=AVALON_INSTANCES)
            bpy.context.scene.collection.children.link(instances)

        placeholder = bpy.data.objects.new(name=placeholder_name, object_data=None)
        placeholder.empty_display_type = 'SINGLE_ARROW'

        if instances:
            instances.objects.link(placeholder)

        imprint(placeholder, placeholder_data)

    def update_placeholder(self, placeholder_item, placeholder_data):
        obj = bpy.data.objects.get(placeholder_item.scene_identifier)
        if not obj:
            raise ValueError("No objects found")

        new_values = {}
        for key, value in placeholder_data.items():
            placeholder_value = placeholder_item.data.get(key)
            if value != placeholder_value:
                new_values[key] = value
                placeholder_item.data[key] = value

        placeholder_name = self._create_placeholder_name(placeholder_data)
        obj.name = placeholder_name
        imprint(obj, new_values)

    def collect_placeholders(self):
        output = []
        scene_placeholders = self._collect_scene_placeholders()
        for obj_name, placeholder_data in scene_placeholders.items():
            if placeholder_data.get("plugin_identifier") != self.identifier:
                continue

            output.append(
                LoadPlaceholderItem(obj_name, placeholder_data, self)
            )

        return output

    def populate_placeholder(self, placeholder):
        self.populate_create_placeholder(placeholder)

    def repopulate_placeholder(self, placeholder):
        self.populate_create_placeholder(placeholder)

    def get_placeholder_options(self, options=None):
        return self.get_create_plugin_options(options)

    def post_placeholder_process(self, placeholder, failed):
        """Add the placehodlers into a dedicated storage collection
        """
        placeholder_coll = bpy.data.collections.get(AVALON_PLACEHOLDER)
        if not placeholder_coll:
            placeholder_coll = bpy.data.collections.new(name=AVALON_PLACEHOLDER)
            bpy.context.scene.collection.children.link(placeholder_coll)

        # Get the corresponding placerholder object in scene
        obj = bpy.data.objects.get(placeholder.scene_identifier)
        if not obj:
            return

        # Get its parent
        parent = get_object_parent_collections(obj)
        if not parent:
            return

        # Unlink from parent and link to storage collection
        parent.objects.unlink(obj)
        placeholder_coll.objects.link(obj)
        # Save file
        save_file(current_file())

    def delete_placeholder(self, placeholder):
        """Remove placeholder if building was successful"""
        cmds.delete(placeholder.scene_identifier)

    def load_succeed(self, placeholder, container):
        self._parent_in_hierarchy(placeholder, container)

    def _parent_in_hierarchy(self, placeholder, container):
        """Parent loaded container to placeholder's parent.

        Args:
            container (bpy.data.object): Placeholder loaded containers
        """
        from .pipeline import AVALON_INSTANCES
        obj = bpy.data.objects.get(placeholder.scene_identifier)
        if not obj:
            raise ValueError("No object found for {}".format(placeholder.scene_identifier))

        instances = bpy.data.collections.get(AVALON_INSTANCES)
        if not instances:
            instances = bpy.data.collections.new(name=AVALON_INSTANCES)
            bpy.context.scene.collection.children.link(instances)

        instances.objects.link(obj)

def build_workfile_template(*args):
    builder = BlenderTemplateBuilder(registered_host())
    builder.build_template()


def update_workfile_template(*args):
    builder = BlenderTemplateBuilder(registered_host())
    builder.rebuild_template()


def get_placeholder_to_update(*args):
    host = registered_host()
    builder = BlenderTemplateBuilder(host)
    placeholder_items_by_id = {
        placeholder_item.scene_identifier: placeholder_item
        for placeholder_item in builder.get_placeholders()
    }
    placeholder_items = []
    for obj in get_selection():
        if obj.name in placeholder_items_by_id:
            placeholder_items.append(placeholder_items_by_id[obj.name])

    # TODO show UI at least
    if len(placeholder_items) == 0:
        raise ValueError("No node selected")

    if len(placeholder_items) > 1:
        raise ValueError("Too many selected nodes")

    placeholder_item = placeholder_items[0]

    return placeholder_item
