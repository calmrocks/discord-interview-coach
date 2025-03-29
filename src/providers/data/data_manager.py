from abc import ABC, abstractmethod
from typing import Dict, Any

class DataManager(ABC):
    @abstractmethod
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def save_user_profile(self, profile: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def get_level_config(self) -> Dict[str, Any]:
        pass