import logging
from .data.data_manager import DataManager
from .data.file_data_manager import FileDataManager

logger = logging.getLogger(__name__)

class DataProvider:
    def __init__(self):
        self.data_manager = self._initialize_data_manager()
        logger.info(f"Initialized DataProvider with {self.data_manager.__class__.__name__}")

    def _initialize_data_manager(self) -> DataManager:
        return FileDataManager()

    async def get_user_profile(self, user_id: str):
        return await self.data_manager.get_user_profile(user_id)

    async def save_user_profile(self, profile):
        await self.data_manager.save_user_profile(profile)

    async def get_level_config(self):
        return await self.data_manager.get_level_config()