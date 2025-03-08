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

        super().__init__(
            command_prefix=config.COMMAND_PREFIX,
            intents=intents,
            description="Your professional Discord interview coach"
        )

    async def setup_hook(self):
        """Automatically load all cogs from the cogs directory"""
        # Get the absolute path to the cogs directory
        cogs_dir = Path(__file__).parent / "cogs"

        # Ensure we're looking at the correct directory
        print(f"Loading cogs from: {cogs_dir}")

        # Loop through all python files in the cogs directory
        for file in os.listdir(cogs_dir):
            if file.endswith('.py') and not file.startswith('__'):
                cog_name = file[:-3]  # Remove .py extension
                cog_path = f'src.cogs.{cog_name}'

                try:
                    await self.load_extension(cog_path)
                    print(f'Successfully loaded {cog_path}')
                except Exception as e:
                    print(f'Failed to load {cog_path}: {e}')

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Serving {len(self.guilds)} guilds')
        print(f'Bot is ready to use! Try {config.COMMAND_PREFIX}echo hello')