import bpy
import logging
import subprocess
import os
import re

from openpype.pipeline.anatomy import Anatomy
from openpype.lib import StringTemplate
from openpype.pipeline.context_tools import get_template_data_from_session


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


bl_info = {
    "name": "Set Render Paths",
    "description": "Set global render output paths and update file output nodes for render layers"
                   "based on 'deadline_render' template, this need to be setted in OP",
    "author": "Quad",
    "version": (2, 0),
    "blender": (2, 80, 0),
    "category": "Render",
    "location": "View 3D > UI > Quad",
}


class VIEW3D_PT_SET_RENDER_PATHS(bpy.types.Panel):
    bl_label = "Set Render Paths"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Quad"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.operator("render_paths.set", text="Set Render Paths")
        col.operator("render_paths.show", text="Open Last Render Folder")


class OBJECT_OT_SET_PATHS(bpy.types.Operator):
    bl_idname = "render_paths.set"
    bl_label = "Set Render Path"

    def __init__(self):
        # Check if the template is well setted
        self.anatomy = Anatomy()
        if not self.anatomy.templates.get('deadline_render'):
            raise NotImplemented("'deadline_render' template need to be setted in your project settings")

        self.renders_path_template = self.anatomy.templates.get('deadline_render')
        self.template_session_data = {'root': self.anatomy.roots, **get_template_data_from_session()}

    def execute(self, context):
        scene = context.scene
        scene.render.filepath = self.get_temp_render_path()
        log.info(f"Global output path has been set to '{scene.render.filepath}'")

        # Ensure that the scene has a node tree and it's not None
        if scene.node_tree is None:
            log.error("Scene does not have a valid node tree. Make sure compositing nodes are enabled.")
            return {'CANCELLED'}

        # Loop through all nodes type 'OUTPUT_FILE'
        output_nodes = [node for node in scene.node_tree.nodes if node.type == 'OUTPUT_FILE']
        for output_node in output_nodes:
            # Find the connected render node
            render_node = self._find_render_node(output_node.inputs)

            # Get the render layer name and the output path
            render_layer_name = render_node.layer
            output_path = self.get_render_node_path(render_layer_name)

            # Set the output path for the output node
            output_node.base_path = output_path
            log.info(f"File output path set to '{output_node.base_path}'.")

        return {'FINISHED'}

    def get_temp_render_path(self):
        """ Build the temp render path based on actual context"""
        # Build temp render path, create folder hierarchy
        temp_render_path = StringTemplate.format_template(self.renders_path_template['global_output'], self.template_session_data)
        os.makedirs(os.path.dirname(temp_render_path), exist_ok=True)
        return temp_render_path

    def get_render_node_path(self, render_layer_name):
        """ Build the render node path based on actual context"""
        # Build render node folder template
        self.template_session_data.update({"render_layer_name": render_layer_name})
        render_node_folder_path = StringTemplate.format_template(self.renders_path_template['folder'], self.template_session_data)

        # Get versions
        if not os.path.exists(render_node_folder_path):
            self.template_session_data.update({'version': 1})
        else:
            latest_version = 1
            regex = fr'v(\d{{{self.renders_path_template["version_padding"]}}})$'
            for version in os.listdir(render_node_folder_path):
                match = re.search(regex, version)
                if match:
                    latest_version = max(latest_version, int(match.group(1)) + 1)# Increment the highest version number
            # Update the template data with the latest version
            self.template_session_data.update({'version': latest_version})

        # Build render node path and create file architecture if not exists
        render_node_path = StringTemplate.format_template(self.renders_path_template['node_output'], self.template_session_data)
        os.makedirs(os.path.dirname(render_node_path), exist_ok=True)
        return render_node_path

    def _find_render_node(self, node_inputs):
        """ recursive method to identify and find 'R_LAYERS' nodes """
        # Recursively search for a node of type 'R_LAYERS'
        for node_input in node_inputs:
            for link in node_input.links:
                target_node = link.from_node
                if target_node.type == 'R_LAYERS':
                    return target_node
                # Recursively search the inputs of the target node
                result = self._find_render_node(target_node.inputs)
                if result:
                    return result


class OBJECT_OT_OPEN_RENDER_FOLDER(bpy.types.Operator):
    bl_idname = "render_paths.show"
    bl_label = "Open Last Render Folder"

    def execute(self, context):
        latest_render_path = self.get_latest_render_path()

        if not os.path.exists(latest_render_path):
            self.report({'ERROR'}, f"File '{latest_render_path}' not found")
            return {'CANCELLED'}

        subprocess.Popen(rf'explorer "{latest_render_path}"', shell=True)
        return {'FINISHED'}

    def get_latest_render_path(self):
        """ Build the render node path based on actual context"""
        # Build render node folder template
        anatomy = Anatomy()
        if not anatomy.templates.get('deadline_render'):
            raise NotImplemented("'deadline_render' template need to be setted in your project settings")

        renders_path_template = anatomy.templates.get('deadline_render')
        template_session_data = {'root': anatomy.roots, **get_template_data_from_session()}
        # Normalize Path for subprocess purpose
        return os.path.normpath(StringTemplate.format_template(renders_path_template['folder'], template_session_data))


def register():
    bpy.utils.register_class(VIEW3D_PT_SET_RENDER_PATHS)
    bpy.utils.register_class(OBJECT_OT_SET_PATHS)
    bpy.utils.register_class(OBJECT_OT_OPEN_RENDER_FOLDER)


def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_SET_RENDER_PATHS)
    bpy.utils.unregister_class(OBJECT_OT_SET_PATHS)
    bpy.utils.unregister_class(OBJECT_OT_OPEN_RENDER_FOLDER)
