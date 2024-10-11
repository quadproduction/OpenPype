from collections import OrderedDict

from openpype.settings import get_project_settings
from openpype.lib import (
    filter_profiles,
    Logger,
    StringTemplate,
)

def get_resolved_name(
    data,
    template):
    """Resolve template_collections_naming with entered data.

    Args:
        data (Dict[str, Any]): Data to fill template_collections_naming.
        template (list): template to solve

    Returns:
        str: Resolved template
    """
    template_obj = StringTemplate(template)
    # Resolve the template
    output = template_obj.format_strict(data)
    if output:
        return output.normalized()
    return output


def get_entity_prefix(data, project_settings=None):
    """Retrieve the asset_type (entity_type) short name for proper blender naming

    Args:
        data (Dict[str, Any]): Data to fill template_collections_naming.
        project_settings(Dict[str, Any]): Prepared project settings for
            project name. Optional to make processing faster.
    Return:
        str: A string corresponding to the short name for entered entity type
    """

    if not project_settings:
        project_settings = get_project_settings(data["project"]["name"])

    # Get Collection Template Profiles
    try:
        profiles = (
            project_settings
            [data["app"]]
            ["templated_workfile_build"]
            ["entity_collection_matcher"]
            ["profiles"]
        )

    except Exception:
        raise KeyError("Project has no profiles set for entity_collection_matcher")

    profile_key = {"entity_types": data["parent"]}
    profile = filter_profiles(profiles, profile_key)
    # If a profile is found, store the pattern
    if profile.get("entity_prefix"):
        return profile["entity_prefix"]

    return None
