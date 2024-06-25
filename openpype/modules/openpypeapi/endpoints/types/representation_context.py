
from typing import TypedDict


class RepresentationContext(TypedDict):
    project_name: str
    asset_name: str
    task_name: str
    version_number: int
    source: str
