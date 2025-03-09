import discord
from discord.ext import commands
from . import config
import os
import pkgutil
from pathlib import Path

class InterviewCoach(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.reactions = True
        intents.presences = True

        super().__init__(
            command_prefix=config.COMMAND_PREFIX,
            intents=intents,
            description="Your professional Discord interview coach"
        )

    async def setup_hook(self):
        """Automatically load all cogs and tasks from the cogs directory"""
        cogs_dir = Path(__file__).parent / "cogs"
        print(f"Loading cogs from: {cogs_dir}")

        # Function to load a cog with proper error handling
        async def load_cog(cog_path: str):
            try:
                await self.load_extension(cog_path)
                print(f'Successfully loaded {cog_path}')
            except Exception as e:
                print(f'Failed to load {cog_path}: {e}')

        # Load regular cogs
        for file in os.listdir(cogs_dir):
            if file.endswith('.py') and not file.startswith('__'):
                cog_name = file[:-3]  # Remove .py extension
                cog_path = f'src.cogs.{cog_name}'
                await load_cog(cog_path)

        # Load task cogs from tasks subdirectory
        tasks_dir = cogs_dir / "tasks"
        if tasks_dir.exists():
            print(f"Loading tasks from: {tasks_dir}")
            for file in os.listdir(tasks_dir):
                if file.endswith('.py') and not file.startswith('__'):
                    task_name = file[:-3]  # Remove .py extension
                    task_path = f'src.cogs.tasks.{task_name}'
                    await load_cog(task_path)

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Serving {len(self.guilds)} guilds')
        print(f'Bot is ready to use! Try {config.COMMAND_PREFIX}echo hello')