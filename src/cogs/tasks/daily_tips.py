from discord.ext import commands, tasks
from datetime import datetime, time
from ...utils.task_scheduler import BaseScheduledTask
import logging

logger = logging.getLogger(__name__)

class DailyTips(commands.Cog, BaseScheduledTask):
    def __init__(self, bot):
        commands.Cog.__init__(self)
        BaseScheduledTask.__init__(self, bot)
        self.task_loop.start()

    def cog_unload(self):
        self.task_loop.cancel()

    def should_run(self) -> bool:
        now = datetime.now(self.timezone)
        # Run once per day at 10 AM
        return now.hour == 10 and now.minute < 30

    async def execute(self):
        """Send daily tips to designated channel"""
        channel = self.bot.get_channel(123456789)  # Replace with your channel ID
        if channel:
            await channel.send("Daily tip placeholder")

    @tasks.loop(minutes=30)
    async def task_loop(self):
        await self.safe_execute()

    @task_loop.before_loop
    async def before_task_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(DailyTips(bot))