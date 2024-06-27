
from openpype.lib.applications import Application
from ..types import ApplicationTypedDict


def get_application_dict(application: Application) -> ApplicationTypedDict:
    """
    Get dictionary holding info from given application instance

    Returns:
        Dict[str, Any]: Dictionary holding application info
    """
    return {
        "full_name": application.full_name,
        "full_label": application.full_label,
        "executable_paths": [app_exec.executable_path for app_exec in application.executables],
        "label": application.label,
        "name": application.name,
    }

