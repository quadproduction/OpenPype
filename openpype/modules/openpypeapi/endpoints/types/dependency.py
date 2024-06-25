
from typing import Optional, TypedDict

from .dependency_type import DependencyType


class Dependency(TypedDict):
    project_name: str
    asset_name: str
    task_name: str
    subset_name: str
    version_number: int
    path: str
    dependency_type: DependencyType
    source: Optional[str] = None
