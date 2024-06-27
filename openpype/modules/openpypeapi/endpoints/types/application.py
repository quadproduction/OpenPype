
from typing import List, TypedDict


class ApplicationTypedDict(TypedDict):
    full_name: str
    full_label: str
    executable_paths: List[str]
    label: str
    name: str
