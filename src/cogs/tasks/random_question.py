from discord.ext import commands, tasks
from datetime import datetime, time
from ...utils.task_scheduler import BaseScheduledTask
import logging

logger = logging.getLogger(__name__)

class RandomQuestions(commands.Cog, BaseScheduledTask):
    def __init__(self, bot):
        commands.Cog.__init__(self)
        BaseScheduledTask.__init__(self, bot)
        self.task_loop.start()

    def cog_unload(self):
        self.task_loop.cancel()

    def should_run(self) -> bool:
        if not self.is_business_hours():
            return False
        return True

    async def execute(self):
        """Send random questions to subscribed users"""
        # Implementation here
        pass

    @tasks.loop(minutes=30)
    async def task_loop(self):
        await self.safe_execute()

    @task_loop.before_loop
    async def before_task_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(RandomQuestions(bot))