

from typing import List, TypedDict


class ProjectSummarized(TypedDict):
    id: str
    name: str
    applications: List[str]
