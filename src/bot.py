import discord
from discord.ext import commands
from . import config

class InterviewCoach(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=config.COMMAND_PREFIX,
            intents=intents,
            description="Your professional Discord interview coach"
        )

    async def setup_hook(self):
        for cog in ['cogs.utils', 'cogs.interview']:
            try:
                await self.load_extension(f'src.{cog}')
                print(f'Successfully loaded {cog}')
            except Exception as e:
                print(f'Failed to load {cog}: {e}')

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Serving {len(self.guilds)} guilds')
        print(f'Bot is ready to use! Try {config.COMMAND_PREFIX}echo hello')