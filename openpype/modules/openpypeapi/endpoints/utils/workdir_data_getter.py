
from openpype.client import get_asset_by_name


def get_workdir_data(project_name: str, asset_name: str, task_name: str):
    """
    Get a dictionary holding data for given task.
    This dictionary is used internally by openpype to fill templates
    with actual data.

    Returns:
        Dict[str, Any]: Dictionary holding task data
    """
    asset = get_asset_by_name(project_name, asset_name)
    if asset is None:
        raise ValueError(f"Could not find asset named '{asset_name}' in project {project_name}")
    
    workdir_data = {
        'project': {'name': project_name},
        'hierarchy': "/".join(asset["data"]["parents"]),
        'asset': asset["name"],
        'task': {'name': task_name},
    }
    return workdir_data
