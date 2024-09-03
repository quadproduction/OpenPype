from openpype.client import get_asset_by_name
from openpype.lib import (
    prepare_template_data,
    EnumDef,
    BoolDef,
    TextDef,
    UISeparatorDef,
    UILabelDef
)
from openpype.pipeline.create import CreatedInstance
from openpype.hosts.tvpaint.api.plugin import TVPaintAutoCreator


class TVPaintCreateRenderCustomlayer(TVPaintAutoCreator):
    family = "render"
    subset_template_family_filter = "renderCustom"
    identifier = "render.custom"
    label = "Custom Render Scene"
    icon = "fa.object-group"
    host_name = "tvpaint"

    # Settings
    mark_for_review = True
    active_on_create = True

    def apply_settings(self, project_settings, system_settings):
        plugin_settings = (
            project_settings["tvpaint"]["create"]["create_custom_render_scene"]
        )
        self.mark_for_review = plugin_settings["mark_for_review"]
        self.review_image_seq = False
        self.active_on_create = plugin_settings["active_on_create"]
        self.default_variant = plugin_settings["default_variant"]
        self.extract_psd = plugin_settings["extract_psd"]
        self.apply_background = False
        self.keep_frame_index = False
        self.exports_types = ['NO', 'scene', 'camera']
        self.export_type = self.exports_types[0]
        self.enabled = plugin_settings.get("enabled", True)
        self.ignore_layers_transparency = plugin_settings.get("ignore_layers_transparency", True)

    def _create_new_instance(self):
        create_context = self.create_context
        host_name = create_context.host_name
        project_name = create_context.get_current_project_name()
        asset_name = create_context.get_current_asset_name()
        task_name = create_context.get_current_task_name()

        asset_doc = get_asset_by_name(project_name, asset_name)
        subset_name = self.get_subset_name(
            self.default_variant,
            task_name,
            asset_doc,
            project_name,
            host_name
        )
        data = {
            "asset": asset_name,
            "task": task_name,
            "variant": self.default_variant,
            "creator_attributes": {
                "mark_for_review": self.mark_for_review,
                "apply_background": self.apply_background,
                "extract_psd": self.extract_psd
            },
            "label": self._get_label(subset_name),
            "active": self.active_on_create
        }

        new_instance = CreatedInstance(
            self.family, subset_name, data, self
        )
        instances_data = self.host.list_instances()
        instances_data.append(new_instance.data_to_store())
        self.host.write_instances(instances_data)
        self._add_instance_to_context(new_instance)
        return new_instance

    def create(self):
        existing_instance = None
        for instance in self.create_context.instances:
            if instance.creator_identifier == self.identifier:
                existing_instance = instance
                break

        if existing_instance is None:
            return self._create_new_instance()

        create_context = self.create_context
        host_name = create_context.host_name
        project_name = create_context.get_current_project_name()
        asset_name = create_context.get_current_asset_name()
        task_name = create_context.get_current_task_name()

        if (
            existing_instance["asset"] != asset_name
            or existing_instance["task"] != task_name
        ):
            asset_doc = get_asset_by_name(project_name, asset_name)
            subset_name = self.get_subset_name(
                existing_instance["variant"],
                task_name,
                asset_doc,
                project_name,
                host_name,
                existing_instance
            )
            existing_instance["asset"] = asset_name
            existing_instance["task"] = task_name
            existing_instance["subset"] = subset_name

        existing_instance["label"] = self._get_label(existing_instance["subset"])

    def _get_label(self, subset_name):
        try:
            subset_name = subset_name.format(**prepare_template_data({}))
        except (KeyError, ValueError):
            pass

        return subset_name

    def get_dynamic_data(self, variant, *args, **kwargs):
        dynamic_data = super().get_dynamic_data(variant, *args, **kwargs)
        return dynamic_data

    def get_instance_attr_defs(self):
        return [
            BoolDef(
                "mark_for_review",
                label="Review Publish",
                default=self.mark_for_review
            ),
            BoolDef(
                "review_image_seq",
                label="Review Media Type: OFF -> video | ON -> Img Seq",
                default=self.review_image_seq
            ),
            BoolDef(
                "keep_frame_index",
                label="Keep actual frame index in Files/Review",
                default=self.keep_frame_index
            ),
            EnumDef(
                "export_type",
                self.exports_types,
                label="Export Quick Review Through",
                default=self.export_type
            ),
            UISeparatorDef("layer_options"),
            UISeparatorDef("layer_options_01"),
            UILabelDef(label="Export Options"),
            BoolDef(
                "ignore_layers_transparency",
                label="All Layers Opacity = 100",
                default=self.ignore_layers_transparency
            ),
            BoolDef(
                "apply_background",
                label="Apply BG Color (as defined in settings)",
                default=self.apply_background
            ),
            TextDef(
                "custom_frames",
                label="Custom Frames Export",
                placeholder="[1-15], 18, 20"
            ),
            BoolDef(
                "extract_psd",
                label="Extract PSD",
                default=self.extract_psd
            )
        ]
