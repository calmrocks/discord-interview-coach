import os
from dotenv import load_dotenv

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

# Parse daily tips channel IDs
DAILY_TIPS_CHANNEL_IDS = [
    int(id.strip())
    for id in os.getenv('DAILY_TIPS_CHANNEL_IDS', '').split(',')
    if id.strip().isdigit()
]

# Ensure required environment variables are set
if not DISCORD_TOKEN:
    raise ValueError("No Discord token found in environment variables")

if not TEST_USER_IDS:
    raise ValueError("No test user IDs found in environment variables")

if not DAILY_TIPS_CHANNEL_IDS:
    raise ValueError("No daily tips channel IDs found in environment variables")
