

from typing import List, TypedDict


class AssetSummarized(TypedDict):
    id: str
    name: str
    entity_type: str
    ftrack_id: str
    hierarchy: str
