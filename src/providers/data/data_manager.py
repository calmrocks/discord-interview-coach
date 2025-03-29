from abc import ABC, abstractmethod
from typing import Dict, List, Any

class DataManager(ABC):
    @abstractmethod
    async def save_user_profile(self, profile: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        pass