import bpy
import logging
import subprocess

from openpype.pipeline.anatomy import Anatomy
from openpype.lib import StringTemplate
from openpype.pipeline.context_tools import get_template_data_from_session
import os
import re

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


bl_info = {
    "name": "Render Playblast",
    "description": "Render sequences of images + video, with OpenGL, from viewport or camera view"
                    "based on 'deadline_render' template, this need to be setted in OP",
    "author": "Quad",
    "version": (2, 0),
    "blender": (2, 80, 0),
    "category": "Render",
    "location": "View 3D > UI> Quad",
}

RENDER_TYPES = {
    "PNG": {"extension": "####.png"},
    "FFMPEG": {"extension": "mp4", "container": "MPEG4"}
}


# Define the All The Playblast Properties
class PlayblastSettings(bpy.types.PropertyGroup):
    use_camera_view: bpy.props.BoolProperty(
        name="Use Camera View",
        description="Use camera view for playblast",
        default=False
    )
    use_transparent_bg: bpy.props.BoolProperty(
        name="Use Transparent Background",
        description="Render playblast with transparent background",
        default=False
    )


# Define the Playblast UI Panel
class VIEW3D_PT_RENDER_PLAYBLAST(bpy.types.Panel):
    bl_label = "Render Playblast"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Quad"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        playblast_settings = scene.playblast_settings  # Access the PlayblastSettings

        col = layout.column()
        col.prop(playblast_settings, "use_camera_view")  # Access property from PlayblastSettings
        col.prop(playblast_settings, "use_transparent_bg")  # Access property from PlayblastSettings
        col.operator("playblast.render", text="Render Playblast")
        col.operator("playblast.open", text="Open Last Playblast Folder")


class OBJECT_OT_RENDER_PLAYBLAST(bpy.types.Operator):
    bl_idname = "playblast.render"
    bl_label = "Render Playblast"

    def execute(self, context):
        scene = context.scene
        region = self.get_view_3D_region()

        # Store the original settings to restore them later
        render_filepath = scene.render.filepath
        file_format = scene.render.image_settings.file_format
        file_extension_use = scene.render.use_file_extension
        engine = scene.render.engine
        film_transparent = scene.render.film_transparent

        # Apply camera view if needed
        if region and scene.playblast_settings.use_camera_view:
            perspective_region = region.view_perspective
            region.view_perspective = "CAMERA"

        # Disable file extension for playblast
        scene.render.use_file_extension = False

        # Apply transparent background settings if needed
        if scene.playblast_settings.use_transparent_bg:
            scene.render.engine = "CYCLES"
            scene.render.film_transparent = True
            scene.render.image_settings.color_mode = "RGBA"

        # Render playblast for each file format
        is_version_already_bumped = False
        for file_format, options in RENDER_TYPES.items():
            scene.render.image_settings.file_format = file_format
            scene.render.filepath = self.get_playblast_path(options['extension'], is_version_already_bumped)
            is_version_already_bumped = True

            # Apply container settings for ffmpeg if needed
            container = options.get('container')
            if container:
                scene.render.ffmpeg.format = container

            logging.info(f"{'Camera view' if scene.playblast_settings.use_camera_view else 'Viewport'} rendering at: {scene.render.filepath}")
            result = bpy.ops.render.opengl(animation=True)
            if result != {"FINISHED"}:
                logging.error(f"Error rendering with file_format {file_format} using OpenGL")
                break

        # Restore the original settings
        scene.render.filepath = render_filepath
        scene.render.image_settings.file_format = file_format
        scene.render.use_file_extension = file_extension_use
        if region and scene.playblast_settings.use_camera_view:
            region.view_perspective = perspective_region

        if scene.playblast_settings.use_transparent_bg:
            # reset to memorized parameters for render
            scene.render.engine = engine
            scene.render.film_transparent = film_transparent
            scene.render.image_settings.color_mode = 'RGB'
        return {"FINISHED"}

    def get_view_3D_region(self):
        """Find the VIEW_3D region and return its region_3d space."""
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        return space.region_3d
        return None

    def get_playblast_path(self, extension, is_version_already_bumped=False):
        """ Build the playblast path based on actual context"""
        # Get Project Anatomy in order to access templates
        anatomy = Anatomy()
        playblast_template = anatomy.templates.get('playblast')
        if not playblast_template:
            raise NotImplemented("'playblast' template need to be setted in your project settings")

        # Build data dict to fill the template later
        template_data = {'ext': extension}
        template_data.update(get_template_data_from_session())
        template_data.update({'root': anatomy.roots})

        # Build playblast Folder Template
        playblast_folder = StringTemplate.format_template(playblast_template['folder'], template_data)

        # Get versions
        if not os.path.exists(os.path.dirname(playblast_folder)):
            template_data.update({'version': 1})
        else:
            latest_version = 1
            regex = fr'v(\d{{{playblast_template["version_padding"]}}})$'
            for version in os.listdir(os.path.dirname(playblast_folder)):
                match = re.search(regex, version)
                if match:
                    version_num = int(match.group(1))
                    if not is_version_already_bumped:
                        latest_version = max(latest_version, version_num + 1)  # Increment the highest version number
                    else:
                        latest_version = max(latest_version, version_num)
            # Update the template data with the latest version
            template_data.update({'version': latest_version})

        # Build playblast path and create file architecture if not exists
        playblast_path = StringTemplate.format_template(playblast_template['path'], template_data)
        os.makedirs(os.path.dirname(playblast_path), exist_ok=True)
        return playblast_path


class OBJECT_OT_OPEN_PLAYBLAST_FOLDER(bpy.types.Operator):
    bl_idname = "playblast.open"
    bl_label = "Open Last Playblast Folder"

    def execute(self, context):
        # Get the path to the most recent playblast folder
        latest_playblast_filepath = self.get_latest_playblast_path()

        if not os.path.exists(latest_playblast_filepath):
            self.report({'ERROR'}, f"File '{latest_playblast_filepath}' not found")
            return {'CANCELLED'}

        subprocess.Popen(f'explorer "{latest_playblast_filepath}"', shell=True)
        return {'FINISHED'}

    def get_latest_playblast_path(self):
        # Get Project Anatomy in order to access templates
        anatomy = Anatomy()
        playblast_template = anatomy.templates.get('playblast')
        if not playblast_template:
            raise NotImplemented("Playblast template need to be setted in your project settings")

        # Build data dict to fill the template later
        template_data = get_template_data_from_session()
        template_data.update({'root': anatomy.roots})

        # Build playblast folder template
        playblast_folder = StringTemplate.format_template(playblast_template['folder'], template_data)

        # Get versions
        if not os.path.exists(os.path.dirname(playblast_folder)):
            return ""
        else:
            latest_version = 1
            # Build regex based on padding's project
            regex = fr'v(\d{{{playblast_template["version_padding"]}}})$'
            for version in os.listdir(os.path.dirname(playblast_folder)):
                match = re.search(regex, version)
                if match:
                    latest_version = max(latest_version, int(match.group(1)))
            # Update the template data with the latest version
            template_data.update({'version': latest_version})

        # Build playblast path and create file architecture if not exists
        return os.path.normpath(StringTemplate.format_template(playblast_template['folder'], template_data))


def register():
    bpy.utils.register_class(PlayblastSettings)
    bpy.types.Scene.playblast_settings = bpy.props.PointerProperty(type=PlayblastSettings)
    bpy.utils.register_class(VIEW3D_PT_RENDER_PLAYBLAST)
    bpy.utils.register_class(OBJECT_OT_RENDER_PLAYBLAST)
    bpy.utils.register_class(OBJECT_OT_OPEN_PLAYBLAST_FOLDER)


def unregister():
    bpy.utils.unregister_class(PlayblastSettings)
    del bpy.types.Scene.playblast_settings  # Remove the property from the scene
    bpy.utils.unregister_class(VIEW3D_PT_RENDER_PLAYBLAST)
    bpy.utils.unregister_class(OBJECT_OT_RENDER_PLAYBLAST)
    bpy.utils.unregister_class(OBJECT_OT_OPEN_PLAYBLAST_FOLDER)
