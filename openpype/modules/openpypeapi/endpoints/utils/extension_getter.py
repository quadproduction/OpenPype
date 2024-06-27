
from openpype.modules import ModulesManager


def get_extensions(application_name: str):
    """
    Get all extensions for application with given name.

    Returns:
        List[str]: Extensions used for workfiles with dot.
    """
    module_manager = ModulesManager()
    application_module = module_manager.get_host_module(application_name)
    if application_module is None:
        raise ValueError(f"No module found for appplication '{application_name}'")
    extensions = application_module.get_workfile_extensions()
    return extensions
