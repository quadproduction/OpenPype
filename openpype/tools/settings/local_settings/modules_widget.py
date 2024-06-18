from qtpy import QtWidgets
from .widgets import (
    ExpandingWidget
)
from openpype.tools.settings import CHILD_OFFSET

ALLOWED_MODULES = ["deadline"]

class ModuleWidget(QtWidgets.QWidget):

    def __init__(
        self, module_name, label, entity, parent
    ):
        self.module_key = label.lower()

        super(ModuleWidget, self).__init__(parent)

        expanding_widget = ExpandingWidget(module_name, self)
        content_widget = QtWidgets.QWidget(expanding_widget)
        content_layout = QtWidgets.QHBoxLayout(content_widget)
        content_layout.setContentsMargins(CHILD_OFFSET, 5, 0, 0)

        expanding_widget.set_content_widget(content_widget)

        # Add expanding widget to main layout
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(expanding_widget)

        label_widget = QtWidgets.QLabel(label)
        self.checkbox_widget = QtWidgets.QCheckBox()
        self.checkbox_widget.setChecked(entity.value)

        content_layout.addWidget(label_widget)
        content_layout.addWidget(self.checkbox_widget)
        content_layout.addStretch()

    def update_local_settings(self, value):
        if value is None:
            return

        elif not isinstance(value, dict):
            print("Got invalid value type {}. Expected {}".format(
                type(value), dict
            ))
            return

        self.checkbox_widget.setChecked(value.get('enabled', False))

    def settings_value(self):
        value = self.checkbox_widget.isChecked()
        return {self.module_key: value}


class LocalModulesWidgets(QtWidgets.QWidget):
    def __init__(self, system_settings_entity, parent):
        super(LocalModulesWidgets, self).__init__(parent)

        self.widgets_by_module_name = {}
        self.system_settings_entity = system_settings_entity

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.content_layout = layout

    def _reset_app_widgets(self):
        while self.content_layout.count() > 0:
            item = self.content_layout.itemAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setVisible(False)
            self.content_layout.removeItem(item)
        self.widgets_by_module_name.clear()

        for module_name, entity in self._valid_modules():
            enabled_entity = next(
                (
                    value for key, value in entity.items()
                    if key == "enabled"
                ), None
            )

            if not enabled_entity: continue

            group_widget = ModuleWidget(
                module_name=module_name,
                label="Enabled",
                entity=enabled_entity,
                parent=self
            )

            self.widgets_by_module_name[module_name] = group_widget
            self.content_layout.addWidget(group_widget)

    def _valid_modules(self):
        return {
            module_name: entity for module_name, entity
            in self.system_settings_entity["modules"].items()
            if module_name in ALLOWED_MODULES
        }.items()

    def update_local_settings(self, value):
        if not value:
            value = {}

        self._reset_app_widgets()

        for group_name, widget in self.widgets_by_module_name.items():
            widget.update_local_settings(value.get(group_name))

    def settings_value(self):
        output = {}
        for module_name, widget in self.widgets_by_module_name.items():
            value = widget.settings_value()
            if value:
                output[module_name] = value
        if not output:
            return None
        return output
