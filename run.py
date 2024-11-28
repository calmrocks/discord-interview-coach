import asyncio
from src.bot import InterviewCoach
from src.config import DISCORD_TOKEN

async def main():
    bot = InterviewCoach()
    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())