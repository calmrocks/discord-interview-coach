import asyncio
from src.bot import InterviewCoach
from src.config import DISCORD_TOKEN, LOGGING_CONFIG
import logging
import logging.config

try:
    logging.config.dictConfig(LOGGING_CONFIG)
except Exception as e:
    print(f"Error in logging configuration: {e}")
    sys.exit(1)



async def main():
    bot = InterviewCoach()
    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())