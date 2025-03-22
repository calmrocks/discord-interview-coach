import os
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()

# Bot Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')

# Parse test user IDs from comma-separated string to list of integers
TEST_USER_IDS = [
    int(id.strip())
    for id in os.getenv('TEST_USER_IDS', '').split(',')
    if id.strip().isdigit()
]

def get_channel_ids(env_var: str) -> List[int]:
    """Convert comma-separated channel IDs from env to list of ints"""
    channel_ids_str = os.getenv(env_var, '')
    if not channel_ids_str:
        return []
    return [int(channel_id) for channel_id in channel_ids_str.split(',') if channel_id]

DAILY_TIPS_CHANNEL_IDS = get_channel_ids('DAILY_TIPS_CHANNEL_IDS')
GAME_CHANNELS_IDS = get_channel_ids('GAME_CHANNELS_IDS')

# Ensure required environment variables are set
if not DISCORD_TOKEN:
    raise ValueError("No Discord token found in environment variables")

if not TEST_USER_IDS:
    raise ValueError("No test user IDs found in environment variables")

if not DAILY_TIPS_CHANNEL_IDS:
    raise ValueError("No daily tips channel IDs found in environment variables")

if not GAME_CHANNELS_IDS:
    raise ValueError("No game channel IDs found in environment variables")
