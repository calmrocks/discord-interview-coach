import json
from pathlib import Path
from .data_manager import DataManager
from typing import Dict, Any

class FileDataManager(DataManager):
    DATA_DIR = Path("data/user_data")
    RECORDS_DIR = DATA_DIR / "records"
    CONFIG_DIR = DATA_DIR / "configs"

    USER_PROFILES_FILE = RECORDS_DIR / "user_profiles.jsonl"
    LEVEL_CONFIG_FILE = CONFIG_DIR / "level_config.json"

    def __init__(self):
        self.RECORDS_DIR.mkdir(parents=True, exist_ok=True)
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        try:
            with open(self.USER_PROFILES_FILE, 'r') as f:
                for line in f:
                    profile = json.loads(line)
                    if profile['user_id'] == user_id:
                        return profile
            # If user not found, create a new profile
            return {
                'user_id': user_id,
                'total_coins': 0,
                'current_streak': {'count': 0, 'last_activity_date': '1970-01-01'},
                'last_check_in_date': '1970-01-01'
            }
        except FileNotFoundError:
            return {
                'user_id': user_id,
                'total_coins': 0,
                'current_streak': {'count': 0, 'last_activity_date': '1970-01-01'},
                'last_check_in_date': '1970-01-01'
            }

    async def save_user_profile(self, profile: Dict[str, Any]) -> None:
        profiles = []
        try:
            with open(self.USER_PROFILES_FILE, 'r') as f:
                profiles = [json.loads(line) for line in f]
        except FileNotFoundError:
            pass

        # Update or add the profile
        for i, p in enumerate(profiles):
            if p['user_id'] == profile['user_id']:
                profiles[i] = profile
                break
        else:
            profiles.append(profile)

        with open(self.USER_PROFILES_FILE, 'w') as f:
            for p in profiles:
                f.write(json.dumps(p) + '\n')

    async def get_level_config(self) -> Dict[str, Any]:
        with open(self.LEVEL_CONFIG_FILE, 'r') as f:
            return json.load(f)