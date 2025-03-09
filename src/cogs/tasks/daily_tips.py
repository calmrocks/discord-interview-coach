from discord.ext import commands, tasks
from datetime import datetime, time
from ...utils.task_scheduler import BaseScheduledTask
from ...config.task_config import TASK_CONFIG
import logging
from ...providers.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

class DailyTips(commands.Cog, BaseScheduledTask):
    def __init__(self, bot, llm_provider):
        commands.Cog.__init__(self)
        BaseScheduledTask.__init__(self, bot)
        self.llm_provider = llm_provider
        self.task_loop.start()

    def cog_unload(self):
        self.task_loop.cancel()

    async def execute(self):
        """Generate and send daily tech tip to all designated channels"""
        channel_ids = TASK_CONFIG['daily_tips']['channel_ids']
        logger.info(f"Executing daily tip task for channels: {channel_ids}")

        try:
            # Generate the daily tip using llm_provider
            daily_tip = await self.llm_provider.create_daily_tip()

            for channel_id in channel_ids:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    try:
                        # Split long messages if needed
                        if len(daily_tip) > 2000:
                            chunks = [daily_tip[i:i+1990] for i in range(0, len(daily_tip), 1990)]
                            for chunk in chunks:
                                await channel.send(chunk)
                        else:
                            await channel.send(daily_tip)
                        logger.info(f"Sent daily tip to channel {channel_id}")
                    except Exception as e:
                        logger.error(f"Failed to send daily tip to channel {channel_id}: {e}")
                else:
                    logger.warning(f"Could not find channel with ID {channel_id}")

        except Exception as e:
            logger.error(f"Failed to execute daily tip task: {e}")

    @tasks.loop(minutes=30)
    async def task_loop(self):
        await self.safe_execute()

    @task_loop.before_loop
    async def before_task_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    llm_provider = LLMProvider()
    await bot.add_cog(DailyTips(bot, llm_provider))