import copy
import collections

from .lib import (
    WRAPPER_TYPES,
    OverrideState,
    NOT_SET
)
from openpype.settings.constants import (
    METADATA_KEYS,
    M_OVERRIDEN_KEY,
    KEY_REGEX
)
from . import (
    BaseItemEntity,
    ItemEntity,
    BoolEntity,
    GUIEntity
)
from .exceptions import (
    SchemaDuplicatedKeys,
    EntitySchemaError,
    InvalidKeySymbols
)


example_schema = {
    "type": "dict-conditional",
    "key": "KEY",
    "label": "LABEL",
    "enum_key": "type",
    "enum_label": "label",
    "enum_children": [
        {
            "key": "action",
            "label": "Action",
            "children": [
                {
                    "type": "text",
                    "key": "key",
                    "label": "Key"
                },
                {
                    "type": "text",
                    "key": "label",
                    "label": "Label"
                },
                {
                    "type": "text",
                    "key": "command",
                    "label": "Comand"
                }
            ]
        },
        {
            "key": "menu",
            "label": "Menu",
            "children": [
                {
                    "type": "list",
                    "object_type": "text"
                }
            ]
        },
        {
            "key": "separator",
            "label": "Separator"
        }
    ]
}


class DictConditionalEntity(ItemEntity):
    schema_types = ["dict-conditional"]
    _default_label_wrap = {
        "use_label_wrap": False,
        "collapsible": False,
        "collapsed": True
    }

    def __getitem__(self, key):
        """Return entity inder key."""
        return self.non_gui_children[self.current_enum][key]

    def __setitem__(self, key, value):
        """Set value of item under key."""
        child_obj = self.non_gui_children[self.current_enum][key]
        child_obj.set(value)

    def __iter__(self):
        """Iter through keys."""
        for key in self.keys():
            yield key

    def __contains__(self, key):
        """Check if key is available."""
        return key in self.non_gui_children[self.current_enum]

    def get(self, key, default=None):
        """Safe entity getter by key."""
        return self.non_gui_children[self.current_enum].get(key, default)

    def keys(self):
        """Entity's keys."""
        keys = list(self.non_gui_children[self.current_enum].keys())
        keys.insert(0, [self.current_enum])
        return keys

    def values(self):
        """Children entities."""
        values = [
            self.enum_entity
        ]
        for child_entiy in self.non_gui_children[self.current_enum].values():
            values.append(child_entiy)
        return values

    def items(self):
        """Children entities paired with their key (key, value)."""
        items = [
            (self.enum_key, self.enum_entity)
        ]
        for key, value in self.non_gui_children[self.current_enum].items():
            items.append((key, value))
        return items

    def set(self, value):
        """Set value."""
        new_value = self.convert_to_valid_type(value)
        # First change value of enum key if available
        if self.enum_key in new_value:
            self.enum_entity.set(new_value.pop(self.enum_key))

        for _key, _value in new_value.items():
            self.non_gui_children[self.current_enum][_key].set(_value)

    def _item_initalization(self):
        self._default_metadata = NOT_SET
        self._studio_override_metadata = NOT_SET
        self._project_override_metadata = NOT_SET

        self._ignore_child_changes = False

        # `current_metadata` are still when schema is loaded
        # - only metadata stored with dict item are gorup overrides in
        #   M_OVERRIDEN_KEY
        self._current_metadata = {}
        self._metadata_are_modified = False

        # Children are stored by key as keys are immutable and are defined by
        # schema
        self.valid_value_types = (dict, )
        self.children = collections.defaultdict(list)
        self.non_gui_children = collections.defaultdict(dict)
        self.gui_layout = collections.defaultdict(list)

        if self.is_dynamic_item:
            self.require_key = False

        self.enum_key = self.schema_data.get("enum_key")
        self.enum_label = self.schema_data.get("enum_label")
        self.enum_children = self.schema_data.get("enum_children")

        self.enum_entity = None
        self.current_enum = None

        self._add_children()

    def schema_validations(self):
        """Validation of schema data."""
        if self.enum_key is None:
            raise EntitySchemaError(self, "Key 'enum_key' is not set.")

        if not isinstance(self.enum_children, list):
            raise EntitySchemaError(
                self, "Key 'enum_children' must be a list. Got: {}".format(
                    str(type(self.enum_children))
                )
            )

        if not self.enum_children:
            raise EntitySchemaError(self, (
                "Key 'enum_children' have empty value. Entity can't work"
                " without children definitions."
            ))

        children_def_keys = []
        for children_def in self.enum_children:
            if not isinstance(children_def, dict):
                raise EntitySchemaError((
                    "Children definition under key 'enum_children' must"
                    " be a dictionary."
                ))

            if "key" not in children_def:
                raise EntitySchemaError((
                    "Children definition under key 'enum_children' miss"
                    " 'key' definition."
                ))
            # We don't validate regex of these keys because they will be stored
            #   as value at the end.
            key = children_def["key"]
            if key in children_def_keys:
                # TODO this hould probably be different exception?
                raise SchemaDuplicatedKeys(self, key)
            children_def_keys.append(key)

        for children in self.children.values():
            children_keys = set()
            children_keys.add(self.enum_key)
            for child_entity in children:
                if not isinstance(child_entity, BaseItemEntity):
                    continue
                elif child_entity.key not in children_keys:
                    children_keys.add(child_entity.key)
                else:
                    raise SchemaDuplicatedKeys(self, child_entity.key)

        for children_by_key in self.non_gui_children.values():
            for key in children_by_key.keys():
                if not KEY_REGEX.match(key):
                    raise InvalidKeySymbols(self.path, key)

        super(DictConditionalEntity, self).schema_validations()
        # Trigger schema validation on children entities
        for children in self.children.values():
            for child_obj in children:
                child_obj.schema_validations()

    def _add_children(self):
        """Add children from schema data and repare enum items.

        Each enum item must have defined it's children. None are shared across
        all enum items.

        Nice to have: Have ability to have shared keys across all enum items.

        All children are stored by their enum item.
        """
        # Skip and wait for validation
        if not self.enum_children or not self.enum_key:
            return

        enum_items = []
        valid_enum_items = []
        for item in self.enum_children:
            if isinstance(item, dict) and "key" in item:
                valid_enum_items.append(item)

        first_key = None
        for item in valid_enum_items:
            item_key = item["key"]
            if first_key is None:
                first_key = item_key
            item_label = item.get("label") or item_key
            enum_items.append({item_key: item_label})

        if not enum_items:
            return

        self.current_enum = first_key

        enum_key = self.enum_key or "invalid"
        enum_schema = {
            "type": "enum",
            "multiselection": False,
            "enum_items": enum_items,
            "key": enum_key,
            "label": self.enum_label or enum_key
        }
        enum_entity = self.create_schema_object(enum_schema, self)
        self.enum_entity = enum_entity

        for item in valid_enum_items:
            item_key = item["key"]
            children = item.get("children") or []
            for children_schema in children:
                child_obj = self.create_schema_object(children_schema, self)
                self.children[item_key].append(child_obj)
                self.gui_layout[item_key].append(child_obj)
                if isinstance(child_obj, GUIEntity):
                    continue

                self.non_gui_children[item_key][child_obj.key] = child_obj

    def get_child_path(self, child_obj):
        """Get hierarchical path of child entity.

        Child must be entity's direct children. This must be possible to get
        for any children even if not from current enum value.
        """
        if child_obj is self.enum_entity:
            return "/".join([self.path, self.enum_key])

        result_key = None
        for children in self.non_gui_children.values():
            for key, _child_obj in children.items():
                if _child_obj is child_obj:
                    result_key = key
                    break

        if result_key is None:
            raise ValueError("Didn't found child {}".format(child_obj))

        return "/".join([self.path, result_key])
