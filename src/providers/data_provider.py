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

    async def save_user_profile(self, profile: Dict[str, Any]) -> None:
        """Delegate to data manager with error handling"""
        try:
            await self.data_manager.save_user_profile(profile)
        except Exception as e:
            logger.error(f"Error saving user profile: {e}", exc_info=True)
            raise