from discord.ext import commands, tasks
from datetime import datetime, time
from ...utils.task_scheduler import BaseScheduledTask
from ...config.task_config import TASK_CONFIG
import logging

logger = logging.getLogger(__name__)

class RandomQuestions(commands.Cog, BaseScheduledTask):
    def __init__(self, bot):
        commands.Cog.__init__(self)
        BaseScheduledTask.__init__(self, bot)
        self.task_loop = self.create_task_loop()
        self.task_loop.start()

    def cog_unload(self):
        self.task_loop.cancel()

    async def execute(self):
        """Send random questions to subscribed users"""
        # Implementation here
        pass

async def setup(bot):
    await bot.add_cog(RandomQuestions(bot))