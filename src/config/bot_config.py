import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')

# Ensure required environment variables are set
if not DISCORD_TOKEN:
    raise ValueError("No Discord token found in environment variables")