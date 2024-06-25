
from openpype.pipeline import Anatomy
from openpype.pipeline.workfile import get_workfile_template_key

from .workdir_data_getter import get_workdir_data


def get_dir_path(
        project_anatomy: Anatomy, asset_name: str, task_name: str, application_name: str
    ) -> str:
    """
    Get path to directory on the file system
    """
    workfile_template_key = get_workfile_template_key(
        task_type=task_name,
        host_name=application_name,
        project_name=project_anatomy.project_name
    )
    workdir_data = get_workdir_data(project_anatomy.project_name, asset_name, task_name)

    if workfile_template_key not in project_anatomy.templates_obj:
        raise ValueError(f"Workfile template key not registered in project templates")
    workfile_template = project_anatomy.templates_obj[workfile_template_key]

    if "folder" not in workfile_template:
        raise ValueError(f"Workfile template does not provide 'folder' value")
    dir_template = workfile_template["folder"]
    dir_path = dir_template.format_strict(workdir_data)
    return dir_path
