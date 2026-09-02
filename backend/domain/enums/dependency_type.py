from enum import Enum
from functools import lru_cache


class DependencyType(Enum):
    CALL = 'call'
    STRUCTURAL = 'structural'


    @classmethod
    @lru_cache(maxsize=1)
    def values(cls) -> list[str]:
        return [item.value for item in cls]
