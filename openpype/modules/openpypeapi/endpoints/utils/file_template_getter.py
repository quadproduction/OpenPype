
from openpype.pipeline import Anatomy
from openpype.pipeline.workfile import get_workfile_template_key


def get_file_template(project_anatomy: Anatomy, application_name: str, task_name: str) -> str:
    """
    Get template for file name (as defined in project settings)
    """
    workfile_template_key = get_workfile_template_key(
        task_type=task_name,
        host_name=application_name,
        project_name=project_anatomy.project_name
    )

    if workfile_template_key not in project_anatomy.templates:
        raise ValueError(f"Workfile template key not registered in project templates")
    workfile_template = project_anatomy.templates[workfile_template_key]

    if "file" not in workfile_template:
        raise ValueError(f"Workfile template does not provide 'file' value")
    return workfile_template["file"]
