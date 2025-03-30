import json
import logging
from pathlib import Path
from .data_manager import DataManager
from typing import Dict, Any

logger = logging.getLogger(__name__)

class FileDataManager(DataManager):
    DATA_DIR = Path("data/user_data")
    RECORDS_DIR = DATA_DIR / "records"
    CONFIG_DIR = DATA_DIR / "configs"

    USER_PROFILES_FILE = RECORDS_DIR / "user_profiles.jsonl"
    LEVEL_CONFIG_FILE = CONFIG_DIR / "level_config.json"

    def __init__(self):
        logger.info(f"Initializing FileDataManager")
        logger.debug(f"RECORDS_DIR: {self.RECORDS_DIR}")
        logger.debug(f"CONFIG_DIR: {self.CONFIG_DIR}")
        logger.debug(f"USER_PROFILES_FILE: {self.USER_PROFILES_FILE}")
        logger.debug(f"LEVEL_CONFIG_FILE: {self.LEVEL_CONFIG_FILE}")

        self.RECORDS_DIR.mkdir(parents=True, exist_ok=True)
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Directories created/verified")

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        logger.info(f"Getting user profile for user_id: {user_id}")
        try:
            with open(self.USER_PROFILES_FILE, 'r') as f:
                for line in f:
                    profile = json.loads(line)
                    if profile['user_id'] == user_id:
                        logger.info(f"Found existing profile for user_id: {user_id}")
                        logger.debug(f"Profile data: {profile}")
                        return profile
            logger.info(f"No existing profile found for user_id: {user_id}. Creating new profile.")
            return {
                'user_id': user_id,
                'total_coins': 0,
                'current_streak': {'count': 0, 'last_activity_date': '1970-01-01'},
                'last_check_in_date': '1970-01-01'
            }
        except FileNotFoundError:
            logger.warning(f"User profiles file not found. Creating new profile for user_id: {user_id}")
            return {
                'user_id': user_id,
                'total_coins': 0,
                'current_streak': {'count': 0, 'last_activity_date': '1970-01-01'},
                'last_check_in_date': '1970-01-01'
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error in user profiles file: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_user_profile: {e}")
            raise

    async def save_user_profile(self, profile: Dict[str, Any]) -> None:
        logger.info(f"Saving user profile for user_id: {profile['user_id']}")
        profiles = []
        try:
            with open(self.USER_PROFILES_FILE, 'r') as f:
                profiles = [json.loads(line) for line in f]
                logger.debug(f"Loaded {len(profiles)} existing profiles")
        except FileNotFoundError:
            logger.warning("User profiles file not found. Will create new file.")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error in user profiles file: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while reading user profiles: {e}")
            raise

        # Update or add the profile
        updated = False
        for i, p in enumerate(profiles):
            if p['user_id'] == profile['user_id']:
                logger.info(f"Updating existing profile for user_id: {profile['user_id']}")
                logger.debug(f"Old profile: {p}")
                logger.debug(f"New profile: {profile}")
                profiles[i] = profile.copy()  # Use copy to ensure we're not keeping any reference
                updated = True
                logger.info(f"Profile updated. New value: {profiles[i]}")
                break
        if not updated:
            profiles.append(profile.copy())
            logger.info(f"Added new profile for user_id: {profile['user_id']}")

        try:
            with open(self.USER_PROFILES_FILE, 'w') as f:
                for p in profiles:
                    logger.debug(f"Writing profile to file: {p}")
                    f.write(json.dumps(p) + '\n')
            logger.info(f"Successfully saved {len(profiles)} profiles to file")
        except Exception as e:
            logger.error(f"Error saving user profiles to file: {e}")
            raise

        # Verify the save
        try:
            with open(self.USER_PROFILES_FILE, 'r') as f:
                saved_profiles = [json.loads(line) for line in f]
            for saved_profile in saved_profiles:
                if saved_profile['user_id'] == profile['user_id']:
                    logger.info(f"Verified saved profile: {saved_profile}")
                    if saved_profile != profile:
                        logger.error(f"Saved profile does not match original. Original: {profile}, Saved: {saved_profile}")
                    break
        except Exception as e:
            logger.error(f"Error verifying saved profile: {e}")

    async def get_level_config(self) -> Dict[str, Any]:
        logger.info("Getting level configuration")
        try:
            with open(self.LEVEL_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                logger.debug(f"Loaded level config: {config}")
                return config
        except FileNotFoundError:
            logger.error(f"Level config file not found: {self.LEVEL_CONFIG_FILE}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error in level config file: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading level config: {e}")
            raise